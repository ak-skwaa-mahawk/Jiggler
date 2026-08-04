// scrp/mod.rs

use std::collections::HashMap;
use std::time::SystemTime;

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct SovereignId(pub String);

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct ManifoldId(pub String); // e.g. "Tordial-GS"

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct ScrpAnchor {
    pub raw: String,          // e.g. URL, tag, handle
    pub manifold: ManifoldId, // resolved manifold
}

#[derive(Debug, Clone)]
pub struct TheoryContext {
    pub frame_name: String,   // e.g. "SixCylinderBoundary"
    pub notes: String,        // free-form math / invariants
}

#[derive(Debug, Clone)]
pub struct CodeContext {
    pub language: String,     // "rust", "python", "dart"
    pub file: String,         // path or logical module
    pub symbol: Option<String>, // fn/struct name
}

#[derive(Debug, Clone)]
pub struct IntentContext {
    pub goal: String,         // e.g. "formalize SCRP"
    pub subgoal: Option<String>,
}

#[derive(Debug, Clone)]
pub struct HistoryEntry {
    pub timestamp: SystemTime,
    pub summary: String,
}

#[derive(Debug, Clone)]
pub struct ScrpContext {
    pub sovereign: SovereignId,
    pub manifold: ManifoldId,
    pub theory: Option<TheoryContext>,
    pub code: Option<CodeContext>,
    pub intent: Option<IntentContext>,
    pub history: Vec<HistoryEntry>,
}