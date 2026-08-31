require 'RubyEventBase.rb' ;

#--======================================================================
#++
## RubyGate の制御インターフェース
class SampleEvent < RubyEventBase
  
  #--------------------------------------------------------------
  #++
  ## 初期化。
  def initialize(_event)
    super ;
    pp [:rubyEventConf, @eventDef] ;
  end
  
  def postUpdate(simTime)
    agents = @simulator.getAgentList()
    if agents
      agents.each do |agent|
        begin
          agent.clearRoute() if agent.respond_to?(:clearRoute)
          agent.recalculatePath() if agent.respond_to?(:recalculatePath)
        rescue => e
          Itk.logWarn("Recalc error for agent: #{e}")
        end
      end
      Itk.logInfo("Recalculated routes for #{agents.size()} agents at simTime=#{simTime}")
    end
  end
end