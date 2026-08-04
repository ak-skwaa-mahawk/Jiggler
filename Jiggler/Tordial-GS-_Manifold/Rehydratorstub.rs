pub struct SimpleRehydrator;

impl ScrpRehydrator for SimpleRehydrator {
    fn rehydrate(
        &self,
        prior: Option<ScrpContext>,
        normalized: &NormalizedMessage,
    ) -> ScrpContext {
        match prior {
            Some(mut ctx) => {
                ctx.history.push(HistoryEntry {
                    timestamp: SystemTime::now(),
                    summary: format!("SCRP: {:?}", normalized.intent),
                });
                ctx
            }
            None => ScrpContext {
                sovereign: SovereignId("default-sovereign".into()),
                manifold: ManifoldId(
                    normalized
                        .details
                        .get("prev_manifold")
                        .cloned()
                        .unwrap_or_else(|| "unknown".into()),
                ),
                theory: None,
                code: None,
                intent: Some(IntentContext {
                    goal: normalized.intent.clone(),
                    subgoal: None,
                }),
                history: vec![HistoryEntry {
                    timestamp: SystemTime::now(),
                    summary: "SCRP: new context".into(),
                }],
            },
        }
    }
}