{/* TRINITY VIZ MODULE */}
<div className="module trinity-viz">
  <h3>🌌 Trinity Dynamics — Live Stabilizer</h3>
  <div className="trinity-controls">
    <select onChange={e => fetchTrinityViz(e.target.value)} defaultValue="Balanced">
      <option value="Stable">Stable</option>
      <option value="Responsive">Responsive</option>
      <option value="Balanced">Balanced</option>
      <option value="Amplified">Amplified</option>
    </select>
    <input 
      type="number" 
      placeholder="Custom damping (0.1-1.0)" 
      onBlur={e => fetchTrinityViz("Custom", parseFloat(e.target.value))}
      step="0.05"
    />
  </div>
  <img id="trinity-image" src="" alt="Trinity Harmonics" style={{width:"100%", borderRadius:"8px"}} />
  <pre id="trinity-data" style={{fontSize:"0.85rem", marginTop:"10px"}}></pre>
</div>