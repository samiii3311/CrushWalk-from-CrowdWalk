#!/usr/bin/env python3
"""
patch_crowdwalk.py
Auto-discovers target Java files, writes DynamicAgentLogger.java,
injects custom research hooks, fixes quickstart double-launch, and compiles with Gradle.
"""

import os
from pathlib import Path
import subprocess
import sys


def find_repo_root() -> Path:
    """Finds the root directory of the CrowdWalk repository."""
    candidates = [Path("."), Path("./crowdwalk"), Path("../")]
    for p in candidates:
        if (p / "build.gradle").exists() or (p / "src").exists():
            return p.resolve()
    print("[!] Could not detect CrowdWalk root directory.")
    sys.exit(1)


REPO_DIR = find_repo_root()


def find_file(filename: str) -> Path:
    """Recursively searches for a file by name inside the repository."""
    matches = list(REPO_DIR.rglob(filename))
    if not matches:
        return None
    return matches[0]


def patch_file(filename: str, search: str, replace: str, marker: str = None) -> bool:
    target_path = find_file(filename)
    if not target_path:
        print(f"[!] Error: File '{filename}' not found anywhere in {REPO_DIR}")
        return False

    content = target_path.read_text(encoding="utf-8").replace("\r\n", "\n")
    search_norm = search.replace("\r\n", "\n")
    replace_norm = replace.replace("\r\n", "\n")
    check_marker = (marker or replace_norm).strip()

    if marker and check_marker in content and search_norm not in content:
        print(f"[*] Already patched: {filename}")
        return True

    if search_norm not in content:
        print(f"[!] Search anchor not found in {filename}:\n    '{search_norm[:45]}...'")
        return False

    target_path.write_text(content.replace(search_norm, replace_norm, 1), encoding="utf-8")
    print(f"[+] Successfully patched: {filename}")
    return True


DYNAMIC_AGENT_LOGGER_SRC = r'''package nodagumi.ananPJ.Simulator;

import java.util.*;
import java.io.PrintWriter;
import java.io.FileOutputStream;
import java.io.File;

import nodagumi.ananPJ.Agents.AgentBase;
import nodagumi.ananPJ.misc.SimTime;
import nodagumi.Itk.Itk;
import nodagumi.Itk.Term;

public class DynamicAgentLogger {
    private PrintWriter writer = null;
    private List<String> fields = new ArrayList<>();

    public DynamicAgentLogger(AgentHandler handler) {
        // Constructor maintained for AgentHandler compatibility
    }

    public void init(Term config) {
        if (config != null) {
            // Use getArgTerm for the fields list
            Term fieldListTerm = config.getArgTerm("fields");
            if (fieldListTerm != null && fieldListTerm.isArray()) {
                for (int i = 0; i < fieldListTerm.getArraySize(); i++) {
                    fields.add(fieldListTerm.getNthTerm(i).getString());
                }
            }

            // Use getArgString for the filename
            String filename = config.getArgString("file");
            if (filename == null) filename = "dynamic_metrics.csv";

            try {
                File file = new File(filename);
                File dir = file.getParentFile();
                if (dir != null && !dir.exists()) dir.mkdirs();

                this.writer = new PrintWriter(new FileOutputStream(file), true);
                
                StringBuilder header = new StringBuilder("current_traveling_period,generated_time,agent_id");
                for (String field : fields) {
                    header.append(",").append(field);
                }
                writer.println(header.toString());
                Itk.logInfo("Dynamic Logger initialized", filename);
            } catch (Exception e) {
                Itk.logError("Dynamic Logger Init Error", e.getMessage());
            }
        }
    }

    public void log(AgentBase agent, SimTime time) {
        if (writer != null && agent != null) {
            StringBuilder row = new StringBuilder();
            row.append((int)time.getRelativeTime()).append(",");
            row.append((int)agent.generatedTime.getRelativeTime()).append(",");
            row.append(agent.ID).append(",");
            
            for (int i = 0; i < fields.size(); i++) {
                String key = fields.get(i);
                Object val = null;

                // Priority 1: Check if the key exists as a tag
                if (agent.hasTag(key)) {
                    val = "1";
                } 
                // Priority 2: Check the agent's Term config for the value
                else if (agent.config != null) {
                    val = agent.config.getArg(key);
                }
                
                row.append(val != null ? val.toString().replaceAll(",", ";") : "0");
                if (i < fields.size() - 1) row.append(",");
            }
            writer.println(row.toString());
        }
    }

    public void close() {
        if (writer != null) {
            writer.flush();
            writer.close();
            writer = null;
        }
        Itk.logInfo("Logger","Logger Finished");
    }
}
'''


def ensure_dynamic_agent_logger():
    """Finds the Simulator package directory and writes DynamicAgentLogger.java."""
    handler_path = find_file("AgentHandler.java")
    if not handler_path:
        print("[!] Could not locate AgentHandler.java to place DynamicAgentLogger.java.")
        return False

    target_path = handler_path.parent / "DynamicAgentLogger.java"
    target_path.write_text(DYNAMIC_AGENT_LOGGER_SRC.strip() + "\n", encoding="utf-8")
    print(f"[+] Created/Updated: {target_path.relative_to(REPO_DIR)}")
    return True


def apply_patches():
    print(f">>> Target repository root: {REPO_DIR}")

    # 0. Write DynamicAgentLogger.java
    ensure_dynamic_agent_logger()

    # 1. AgentBase.java
    agent_base_fields = """
    // === Custom: Ghost & Overlap ===
    protected boolean allowOverlap = false;
    public void setAllowOverlap(boolean flag) { this.allowOverlap = flag; }
    public boolean isAllowOverlap() { return allowOverlap; }

    protected boolean ghostMode = false;
    public boolean isGhost() { return ghostMode; }
    public void setGhost(boolean flag) { ghostMode = flag; }
}"""
    patch_file(
        "AgentBase.java",
        search="}\n// ;;; Local Variables:",
        replace=agent_base_fields + "\n// ;;; Local Variables:",
        marker="boolean ghostMode = false;",
    )

    # 2. WalkAgent.java
    patch_file(
        "WalkAgent.java",
        search="protected double calcSocialForce(double dist) {",
        replace="""protected double calcSocialForce(double dist) {
        if (this.isGhost()) return 0.0;""",
        marker="if (this.isGhost()) return 0.0;",
    )

    patch_file(
        "WalkAgent.java",
        search="protected double calcSocialForceToHeading(double dx, double dy) {",
        replace="""protected double calcSocialForceToHeading(double dx, double dy) {
        if (this.isGhost()) return 0.0;""",
        marker="protected double calcSocialForceToHeading(double dx, double dy) {\n        if (this.isGhost()) return 0.0;",
    )

    patch_file(
        "WalkAgent.java",
        search="private double accumulateSocialForces(SimTime currentTime, double lowerBound) {",
        replace="""private double accumulateSocialForces(SimTime currentTime, double lowerBound) {
        if (this.isGhost()) return 0.0;""",
        marker="private double accumulateSocialForces(SimTime currentTime, double lowerBound) {\n        if (this.isGhost()) return 0.0;",
    )

    patch_file(
        "WalkAgent.java",
        search="AgentBase agent = otherLane.get(otherLane.size() - i - 1);",
        replace="""AgentBase agent = otherLane.get(otherLane.size() - i - 1);
                if (agent.isGhost()) continue;""",
        marker="if (agent.isGhost()) continue;",
    )

    patch_file(
        "WalkAgent.java",
        search="for(AgentBase agent : sameLane) {",
        replace="""for(AgentBase agent : sameLane) {
                if (agent.isGhost()) continue;""",
        marker="for(AgentBase agent : sameLane) {\n                if (agent.isGhost()) continue;",
    )

    orig_pred = """            if(agents.size() > 0 && predecessorIndex < agents.size()) {
                // 現在のworkingPlace に前の人がいる場合
                // indexが負の場合は、最後尾の人が直前の人
                if(predecessorIndex < 0) predecessorIndex = 0 ;
                distToPredecessor +=
                    agents.get(predecessorIndex).currentPlace.getAdvancingDistance() ;
                break ;
            }"""

    custom_pred = """            if (agents.size() > 0 && predecessorIndex < agents.size()) {
                AgentBase predecessor = null;
                for (int i = predecessorIndex; i < agents.size(); i++) {
                    AgentBase a = agents.get(i);
                    if (!a.isGhost()) {
                        predecessor = a;
                        break;
                    }
                }
                if (predecessor != null) {
                    distToPredecessor += predecessor.currentPlace.getAdvancingDistance();
                    break;
                }
            }"""
    patch_file(
        "WalkAgent.java",
        search=orig_pred,
        replace=custom_pred,
        marker="AgentBase predecessor = null;",
    )

    # 3. AgentHandler.java
    patch_file(
        "AgentHandler.java",
        search="private EvacuationSimulator simulator;",
        replace="""private EvacuationSimulator simulator;
    private DynamicAgentLogger dynamicLogger = new DynamicAgentLogger(this);""",
        marker="private DynamicAgentLogger dynamicLogger",
    )

    patch_file(
        "AgentHandler.java",
        search="agent.update(currentTime);",
        replace="""agent.update(currentTime);
                dynamicLogger.log(agent, currentTime);
                if (agent.hasTag("crushed") && !agent.hasTag("crushed_logged")) {
                    logCrushedAgent(agent, currentTime);
                    agent.addTag("crushed_logged");
                }""",
        marker="logCrushedAgent(agent, currentTime);",
    )

    patch_file(
        "AgentHandler.java",
        search="setupEvacuatedAgentsLogger() ;",
        replace="""setupEvacuatedAgentsLogger() ;
        setupCrushedAgentsLogger();""",
        marker="setupCrushedAgentsLogger();",
    )

    patch_file(
        "AgentHandler.java",
        search="initEvacuatedAgentsLogger() ;",
        replace="""initEvacuatedAgentsLogger() ;
        initCrushedAgentsLogger();
        dynamicLogger.init(simulator.getProperties().getTerm("dynamic_logging"));""",
        marker="initCrushedAgentsLogger();",
    )

    patch_file(
        "AgentHandler.java",
        search="closeEvacuatedAgentsLogger();",
        replace="""closeEvacuatedAgentsLogger();
        closeCrushedAgentsLogger();
        dynamicLogger.close();""",
        marker="closeCrushedAgentsLogger();",
    )

    crushed_handler_methods = """
    // === Custom: Crushed & Log Helpers ===
    public int numOfCrushed() {
        int crushed = 0;
        for (AgentBase agent : getAllAgentCollection()) {
            if (agent != null && agent.hasTag("crushed")) crushed++;
        }
        return crushed;
    }

    public Logger crushedAgentsLogger = null;
    public static CsvFormatter<AgentBase> crushedAgentsLoggerFormatter = new CsvFormatter<AgentBase>();
    static {
        CsvFormatter<AgentBase> formatter = crushedAgentsLoggerFormatter;
        formatter
            .addColumn(formatter.new Column("generated_time") {
                public String value(AgentBase agent, Object timeObj, Object agentHandlerObj) {
                    return "" + (int)agent.generatedTime.getRelativeTime();
                }})
            .addColumn(formatter.new Column("current_traveling_period") {
                public String value(AgentBase agent, Object timeObj, Object agentHandlerObj) {
                    return "" + (int)((SimTime)timeObj).getRelativeTime();
                }})
            .addColumn(formatter.new Column("pedestrianID") {
                public String value(AgentBase agent, Object timeObj, Object agentHandlerObj) {
                    return agent.getID();
                }})
            .addColumn(formatter.new Column("event_type") {
                public String value(AgentBase agent, Object timeObj, Object agentHandlerObj) {
                    return "CRUSHED";
                }})
            .addColumn(formatter.new Column("current_linkID") {
                public String value(AgentBase agent, Object timeObj, Object agentHandlerObj) {
                    return (agent.getCurrentLink() != null) ? agent.getCurrentLink().getID() : "";
                }})
            .addColumn(formatter.new Column("forward_node") {
                public String value(AgentBase agent, Object timeObj, Object agentHandlerObj) {
                    return (agent.getNextNode() != null) ? agent.getNextNode().getID() : "";
                }})
            .addColumn(formatter.new Column("backward_node") {
                public String value(AgentBase agent, Object timeObj, Object agentHandlerObj) {
                    return (agent.getPrevNode() != null) ? agent.getPrevNode().getID() : "";
                }});
    }

    public void logCrushedAgent(AgentBase agent, SimTime currentTime) {
        if (crushedAgentsLogger != null && agent != null) {
            crushedAgentsLoggerFormatter.outputValueToLoggerInfo(crushedAgentsLogger, agent, currentTime, this);
        }
    }
    private void closeCrushedAgentsLogger() { closeLogger(crushedAgentsLogger); }
    private void setupCrushedAgentsLogger() {}
    private void initCrushedAgentsLogger() {
        try {
            String crushedLogDir = simulator.getProperties().getDirectoryPath("crushed_agents_log_dir", null);
            if (crushedLogDir != null) {
                crushedLogDir = crushedLogDir.replaceFirst("[/\\\\\\\\]+$", "");
                openCrushedAgentsLogger("crushed_agents_log", crushedLogDir);
            }
        } catch(Exception e) {
            Itk.logError("can not setup Crushed Logger", e.getMessage());
            Itk.quitWithStackTrace(e);
        }
    }
    private void openCrushedAgentsLogger(String name, String dirPath) {
        crushedAgentsLogger = openLogger(name, Level.INFO, dirPath + "/log_crushed_agents.csv");
        crushedAgentsLoggerFormatter.outputHeaderToLoggerInfo(crushedAgentsLogger);
    }
}"""
    patch_file(
        "AgentHandler.java",
        search="    public void setupAgentFactoryByRuby(ItkRuby rubyEngine) {\n        for(AgentFactory factory : agentFactoryList) {\n            if(factory instanceof AgentFactoryByRuby) {\n                ((AgentFactoryByRuby)factory).setupRubyEngine(rubyEngine) ;\n            }\n        }\n    }\n}",
        replace="    public void setupAgentFactoryByRuby(ItkRuby rubyEngine) {\n        for(AgentFactory factory : agentFactoryList) {\n            if(factory instanceof AgentFactoryByRuby) {\n                ((AgentFactoryByRuby)factory).setupRubyEngine(rubyEngine) ;\n            }\n        }\n    }\n"
        + crushed_handler_methods,
        marker="numOfCrushed()",
    )

    # 4. EvacuationSimulator.java
    patch_file(
        "EvacuationSimulator.java",
        search='agentHandler.numOfEvacuatedAgents(), agentHandler.getMaxAgentCount());',
        replace='agentHandler.numOfEvacuatedAgents(), agentHandler.getMaxAgentCount(), agentHandler.numOfCrushed(), agentHandler.getMaxAgentCount());',
        marker="agentHandler.numOfCrushed()",
    )
    patch_file(
        "EvacuationSimulator.java",
        search='"Walking: %d  Generated: %d  Evacuated: %d / %d"',
        replace='"Walking: %d  Generated: %d  Evacuated: %d / %d Crushed: %d / %d"',
        marker="Crushed: %d / %d",
    )
    patch_file(
        "EvacuationSimulator.java",
        search='"Walking: %d  Generated: %d  Evacuated(Stuck): %d(%d) / %d"',
        replace='"Walking: %d  Generated: %d  Evacuated(Stuck): %d(%d) / %d Crushed: %d / %d"',
        marker="Crushed: %d / %d",
    )

    # 5. BasicSimulationLauncher.java
    launcher_check = """        finished = simulator.updateEveryTick();
        nodagumi.ananPJ.Simulator.AgentHandler agentHandler = simulator.getAgentHandler();
        boolean aliveFound = false;

        for (AgentBase agent : simulator.getAgentHandler().getAllAgentCollection()){
            if (agent == null) continue;
            if (!agent.hasTag("crushed") && !agent.isEvacuated()){
                aliveFound = true;
                break;
            }
        }

        if (!aliveFound && (agentHandler.numOfCrushed() + agentHandler.numOfEvacuatedAgents() >= agentHandler.getMaxAgentCount())){
            finished = true;
        }"""
    patch_file(
        "BasicSimulationLauncher.java",
        search="finished = simulator.updateEveryTick();",
        replace=launcher_check,
        marker="agentHandler.numOfCrushed() + agentHandler.numOfEvacuatedAgents()",
    )

    # 6. quickstart.sh (Remove duplicate launch command)
    double_launch = """echo "$JAVA $JAVAOPT -Djdk.gtk.version=2 -jar $JAR $*"
$JAVA $JAVAOPT -Djdk.gtk.version=2 -jar $JAR $*

echo "$JAVA $JAVAOPT -Djdk.gtk.version=2 -jar $JAR $*"
$JAVA $JAVAOPT -Djdk.gtk.version=2 -jar $JAR $*"""

    single_launch = """echo "$JAVA $JAVAOPT -Djdk.gtk.version=2 -jar $JAR $*"
$JAVA $JAVAOPT -Djdk.gtk.version=2 -jar $JAR $*"""

    patch_file(
        "quickstart.sh",
        search=double_launch,
        replace=single_launch,
        marker=single_launch,
    )


def run_gradle_build(skip_tests: bool = True):
    print("\n>>> Building CrowdWalk with Gradle...")
    is_windows = sys.platform == "win32"
    gradle_exec = REPO_DIR / ("gradlew.bat" if is_windows else "gradlew")

    if not gradle_exec.exists():
        print(f"[!] Could not find Gradle wrapper at {gradle_exec.resolve()}")
        return False

    if not is_windows:
        os.chmod(gradle_exec, 0o755)

    build_cmd = [str(gradle_exec.resolve()), "build"]
    if skip_tests:
        build_cmd.extend(["-x", "test"])

    result = subprocess.run(build_cmd, cwd=REPO_DIR, check=False)
    if result.returncode == 0:
        print("\n[✓] CrowdWalk patched and built successfully!")
        return True
    else:
        print(f"\n[!] Gradle build exited with code: {result.returncode}")
        return False


if __name__ == "__main__":
    apply_patches()
    run_gradle_build(skip_tests=True)