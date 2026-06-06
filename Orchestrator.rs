pub struct ScrpEngine<R, S, T, H>
where
    R: ScrpAnchorResolver,
    S: ScrpContextStore,
    T: ScrpTranslator,
    H: ScrpRehydrator,
{
    pub resolver: R,
    pub store: S,
    pub translator: T,
    pub rehydrator: H,
}

impl<R, S, T, H> ScrpEngine<R, S, T, H>
where
    R: ScrpAnchorResolver,
    S: ScrpContextStore,
    T: ScrpTranslator,
    H: ScrpRehydrator,
{
    pub fn handle_message(
        &mut self,
        sovereign: SovereignId,
        raw_message: &str,
    ) -> Option<ScrpContext> {
        // 1. Extract anchor(s) from message
        let anchor = extract_anchor(raw_message)
            .and_then(|raw| self.resolver.resolve_anchor(&raw))?;

        // 2. Load last context
        let prior = self.store.load_last(&sovereign, &anchor.manifold);

        // 3. Translate style + message into normalized intent
        let normalized = self.translator.translate(raw_message, prior.as_ref());

        // 4. Rehydrate context
        let new_ctx = self.rehydrator.rehydrate(prior, &normalized);

        // 5. Persist
        self.store.save(new_ctx.clone());

        Some(new_ctx)
    }
}

/// Very simple anchor extractor; you can swap this for a real parser.
fn extract_anchor(raw_message: &str) -> Option<String> {
    raw_message
        .split_whitespace()
        .find(|tok| tok.starts_with("http"))
        .map(|s| s.to_string())
}