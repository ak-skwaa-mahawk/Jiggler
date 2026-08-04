// Added export for Python bridge
#[pyo3::pyfunction]
fn recursive_pi_r_catch_py(keypoints: Vec<f64>) -> PyResult<f64> {
    let guarded = recursive_pi_r_catch(keypoints); // original Floor logic
    Ok(guarded.pi_r_surplus) // returns coherence surplus for audit
}