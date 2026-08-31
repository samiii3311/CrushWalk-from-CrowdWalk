require 'RubyAgentBase.rb'

class SpaceForceAgent < RubyAgentBase
  TriggerFilter = ["update"]

  attr_accessor :personal_space_radius, :firmness

  def initialize(agent, config, fallback)
    super(agent, config, fallback)
    # Access the Properties Handler from the Java Simulator
    props = getSimulator().getProperties()

    # DYNAMIC PARAMETERS: Pull from prop.json with default fallbacks
    # 'personal_space_radius' defines the distance agents try to maintain.
    @personal_space_radius = props.getDouble("personal_space_radius", 1.2)
    
    # 'firmness' defines how strongly they push away when inside that radius.
    @firmness = props.getDouble("firmness", 0.8)
  end

  def update
    my_pos = @javaAgent.getPosition()
    all_agents = getSimulator().getAllAgentCollection()

    all_agents.each do |other|
      next if other == @javaAgent

      dist = my_pos.distance(other.getPosition())

      if dist < @personal_space_radius && dist > 0.1
        pressure = (@personal_space_radius - dist) * @firmness

        # # Apply pressure to engine (THIS replaces manual speed hacks)
        # @javaAgent.exposed(pressure)
      end
    end

    return super()
  end
end