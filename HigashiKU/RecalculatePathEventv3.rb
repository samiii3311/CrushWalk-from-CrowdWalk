# coding: utf-8
## リンク閉鎖に起因する、エージェントのルート再計算指示イベント
require 'RubyEventBase.rb' ;
require 'NetworkMap.rb' ;

# RubyEventBase は ItkUtility を include しています。

class RecalculatePathEventv2 < RubyEventBase
  
  #--------------------------------------------------------------
  #++
  ## 初期化
  def initialize(_event)
    super ;
    # @eventDef には scenario.json のイベント定義が格納されます。
    # 例: { "type":"Ruby", "atTime":"...", "rubyClass": "RecalculateRouteEvent", "linkTag": "closure_target", "name": "LinkClosureEvent" }    
    logWithLevel(:info, nil, "RecalculateRouteOnlyEvent Initialized.", @eventDef) ;
  end
  
  #--------------------------------------------------------------
  #++
  ## イベント発生時に実行される処理
  ## currentTime:: 現在のシミュレーション時間
  ## map:: NetworkMap のインスタンス
  def occur(currentTime, map)
    logWithLevel(:info, nil, "Route Recalculation Event triggered at:", currentTime) ;
    
    # --- 1. シミュレーターオブジェクトの取得 ---
    # RubyEventBase#getSimulator() は Java の EvacuationSimulator インスタンスを返す
    simulator = getSimulator() ;
    
    # --- 2. 全エージェントへのルート再計算の指示 ---
    
    begin
      # EvacuationSimulator.java で定義されている Java メソッドを呼び出し
      logWithLevel(:info, nil, "経路再探索を指示中...") ;
      
      # EvacuationSimulator#recalculatePaths() を呼び出すことで、
      # 内部で buildRoutes() が実行され、全経路探索情報が再構築されます。
      simulator.recalculatePaths() ; 
      
      logWithLevel(:info, nil, "成功：全エージェントの経路再探索が完了しました。") ;
      
    rescue => e
      # Javaメソッドの呼び出しに失敗した場合のログ
      logWithLevel(:error, nil, "Failed to call recalculatePaths() on simulator:", e.message) ;
      # 致命的なエラーとして報告する
      logWithLevel(:fatal, nil, "経路再計算　失敗. Simulation state may be inconsistent.") ;
    end
    
    # イベント処理を終了させるため true を返します。
    return true ;
  end
end # class RecalculateRouteOnlyEvent