pub struct SimpleTranslator;

impl ScrpTranslator for SimpleTranslator {
    fn translate(
        &self,
        raw_message: &str,
        prior: Option<&ScrpContext>,
    ) -> NormalizedMessage {
        let mut details = HashMap::new();

        if raw_message.contains("where was I") {
            details.insert("cue".into(), "restore".into());
        }

        if let Some(ctx) = prior {
            details.insert("prev_manifold".into(), ctx.manifold.0.clone());
        }

        NormalizedMessage {
            intent: "continue_context".into(),
            details,
        }
    }
}