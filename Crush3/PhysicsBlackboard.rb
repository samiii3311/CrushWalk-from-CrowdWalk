require 'singleton'

class PhysicsBlackboard
  include Singleton

  def initialize
    # Hit memory: { victim_id => { aggressor_id => { accel: 0.0, time: 0.0 } } }
    @hits = {}
    
    # Intent memory: { agent_id => accel }
    @intent = {} 

    @masses = {}
  end

  # --- Physical Shockwave Logic (Already exists) ---
  def register_push(aggressor_id, victim_id, accel, current_time)
    tick_time = current_time.getAbsoluteTime()
    @hits[victim_id] ||= {}
    @hits[victim_id][aggressor_id] = { accel: accel, time: tick_time }
  end

  def has_hit?(aggressor_id, victim_id, current_time)
    hit_data = @hits.dig(victim_id, aggressor_id)
    return false if hit_data.nil?
    hit_data[:time] == current_time.getAbsoluteTime()
  end

  def get_hit_accel(aggressor_id, victim_id, current_time)
    return 0.0 unless has_hit?(aggressor_id, victim_id, current_time)
    @hits[victim_id][aggressor_id][:accel]
  end

  # --- NEW: General Acceleration Logic ---
  def log_accel(agent_id, accel)
    @intent[agent_id] = accel
  end

  def get_accel(agent_id)
    return @intent[agent_id] || 0.0
  end

  def log_mass(agent_id, mass)
    @masses[agent_id] = mass
  end

  def get_mass(agent_id)
    # Default to 60.0 if the agent isn't found for some reason
    return @masses[agent_id] || 60.0 
  end
end