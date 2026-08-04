use pyo3::prelude::*;
use pyo3::types::PyAny;
use pyo3::ffi;
use rayon::prelude::*;
use std::slice;

#[pyfunction]
#[pyo3(name = "process_drift_batch_zero_copy")]
fn process_drift_batch_zero_copy(
    _py: Python,
    py_input: &PyAny,
    py_output: &PyAny,
    threshold: f32,
) -> PyResult<u64> {
    let input_slice: &[f32] = unsafe {
        let mut view: ffi::Py_buffer = std::mem::zeroed();
        if ffi::PyObject_GetBuffer(py_input.as_ptr(), &mut view, ffi::PyBUF_SIMPLE) != 0 {
            return Err(PyErr::fetch(_py));
        }
        let len = view.len as usize / std::mem::size_of::<f32>();
        let slice = slice::from_raw_parts(view.buf as *const f32, len);
        ffi::PyBuffer_Release(&mut view);
        slice
    };

    let output_slice: &mut [f32] = unsafe {
        let mut view: ffi::Py_buffer = std::mem::zeroed();
        if ffi::PyObject_GetBuffer(py_output.as_ptr(), &mut view, ffi::PyBUF_WRITABLE) != 0 {
            return Err(PyErr::fetch(_py));
        }
        let len = view.len as usize / std::mem::size_of::<f32>();
        let slice = slice::from_raw_parts_mut(view.buf as *mut f32, len);
        ffi::PyBuffer_Release(&mut view);
        slice
    };

    const CHUNK_SIZE: usize = 131_072;

    let total_oob: u64 = input_slice
        .par_chunks(CHUNK_SIZE)
        .zip(output_slice.par_chunks_mut(CHUNK_SIZE))
        .map(|(in_chunk, out_chunk)| {
            let mut chunk_oob = 0u64;
            let len = in_chunk.len();
            let simd_len = len - (len % 8);
            let mut i = 0;

            while i < simd_len {
                let v0 = in_chunk[i];
                let v1 = in_chunk[i + 1];
                let v2 = in_chunk[i + 2];
                let v3 = in_chunk[i + 3];
                let v4 = in_chunk[i + 4];
                let v5 = in_chunk[i + 5];
                let v6 = in_chunk[i + 6];
                let v7 = in_chunk[i + 7];

                let cond0 = v0.abs() > threshold;
                let cond1 = v1.abs() > threshold;
                let cond2 = v2.abs() > threshold;
                let cond3 = v3.abs() > threshold;
                let cond4 = v4.abs() > threshold;
                let cond5 = v5.abs() > threshold;
                let cond6 = v6.abs() > threshold;
                let cond7 = v7.abs() > threshold;

                out_chunk[i]     = if cond0 { v0 } else { 0.0 };
                out_chunk[i + 1] = if cond1 { v1 } else { 0.0 };
                out_chunk[i + 2] = if cond2 { v2 } else { 0.0 };
                out_chunk[i + 3] = if cond3 { v3 } else { 0.0 };
                out_chunk[i + 4] = if cond4 { v4 } else { 0.0 };
                out_chunk[i + 5] = if cond5 { v5 } else { 0.0 };
                out_chunk[i + 6] = if cond6 { v6 } else { 0.0 };
                out_chunk[i + 7] = if cond7 { v7 } else { 0.0 };

                chunk_oob += (cond0 as u64) + (cond1 as u64) + (cond2 as u64) + (cond3 as u64)
                           + (cond4 as u64) + (cond5 as u64) + (cond6 as u64) + (cond7 as u64);
                i += 8;
            }

            while i < len {
                let v = in_chunk[i];
                if v.abs() > threshold {
                    out_chunk[i] = v;
                    chunk_oob += 1;
                } else {
                    out_chunk[i] = 0.0;
                }
                i += 1;
            }

            chunk_oob
        })
        .sum();

    Ok(total_oob)
}

#[pymodule]
fn jiggler_native(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(process_drift_batch_zero_copy, m)?)?;
    Ok(())
}
