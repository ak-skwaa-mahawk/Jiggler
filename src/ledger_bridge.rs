use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fs::File;
use std::io::Read;

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct RustBlock {
    pub index: u64,
    pub previous_hash: String,
    pub timestamp: f64,
    pub data: serde_json::Value,
    pub nonce: u64,
    pub hash: String,
}

impl RustBlock {
    pub fn calculate_hash(&self) -> String {
        let json_string = serde_json::json!({
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "data": self.data,
            "nonce": self.nonce
        });
        
        let mut hasher = Sha256::new();
        hasher.update(json_string.to_string().as_bytes());
        let result = hasher.finalize();
        
        // Convert the structural generic byte array into a hex string format cleanly
        result.iter().map(|b| format!("{:02x}", b)).collect::<String>()
    }
}

#[pyclass]
pub struct NativeLedgerBridge {
    #[pyo3(get)]
    pub ledger_file: String,
    pub difficulty: usize,
}

#[pymethods]
impl NativeLedgerBridge {
    #[new]
    pub fn new(ledger_file: String, difficulty: usize) -> Self {
        NativeLedgerBridge { ledger_file, difficulty }
    }

    pub fn validate_ledger_file(&self) -> PyResult<bool> {
        let mut file = match File::open(&self.ledger_file) {
            Ok(f) => f,
            Err(_) => return Ok(false),
        };

        let mut contents = String::new();
        if file.read_to_string(&mut contents).is_err() {
            return Ok(false);
        }

        let chain: Vec<RustBlock> = match serde_json::from_str(&contents) {
            Ok(c) => c,
            Err(_) => return Ok(false),
        };

        let target_prefix = "0".repeat(self.difficulty);

        for i in 0..chain.len() {
            let current = &chain[i];

            if current.hash != current.calculate_hash() {
                return Ok(false);
            }

            if !current.hash.starts_with(&target_prefix) {
                return Ok(false);
            }

            if i > 0 {
                let previous = &chain[i - 1];
                if current.previous_hash != previous.hash {
                    return Ok(false);
                }
            }
        }

        Ok(true)
    }

    pub fn mine_block_data(&self, index: u64, previous_hash: String, timestamp: f64, data_json: String) -> PyResult<PyObject> {
        let parsed_data: serde_json::Value = serde_json::from_str(&data_json)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

        let mut block = RustBlock {
            index,
            previous_hash,
            timestamp,
            data: parsed_data,
            nonce: 0,
            hash: String::new(),
        };

        let target_prefix = "0".repeat(self.difficulty);
        block.hash = block.calculate_hash();

        while !block.hash.starts_with(&target_prefix) {
            block.nonce += 1;
            block.hash = block.calculate_hash();
        }

        Python::with_gil(|py| {
            let dict = pyo3::types::PyDict::new_bound(py);
            dict.set_item("index", block.index)?;
            dict.set_item("previous_hash", block.previous_hash)?;
            dict.set_item("timestamp", block.timestamp)?;
            dict.set_item("nonce", block.nonce)?;
            dict.set_item("hash", block.hash)?;
            Ok(dict.into())
        })
    }
}
