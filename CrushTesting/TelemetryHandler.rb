# TelemetryHandler.rb
module TelemetryHandler
  def self.update_telemetry(agent, physics_data)
    config = agent.config
    java_agent = agent.javaAgent

    # 1. Core Physics
    config.setArg("crush_pressure", physics_data[:pressure])
    config.setArg("current_speed", physics_data[:speed])
    
    # 2. Agent State
    config.setArg("agent_status", java_agent.hasTag("crushed") ? "CRUSHED" : "OK")
  end
end