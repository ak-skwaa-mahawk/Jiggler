/// Resolves raw anchors (URLs, tags) into manifolds.
pub trait ScrpAnchorResolver {
    fn resolve_anchor(&self, raw: &str) -> Option<ScrpAnchor>;
}

/// Persistent store for last-known context per (sovereign, manifold).
pub trait ScrpContextStore {
    fn load_last(
        &self,
        sovereign: &SovereignId,
        manifold: &ManifoldId,
    ) -> Option<ScrpContext>;

    fn save(&mut self, context: ScrpContext);
}

/// Translates raw messages + prior context into normalized intent.
pub trait ScrpTranslator {
    /// `raw_message` is the user text; `prior` is last context (if any).
    fn translate(
        &self,
        raw_message: &str,
        prior: Option<&ScrpContext>,
    ) -> NormalizedMessage;
}

/// Rehydrates a live context from prior context + normalized message.
pub trait ScrpRehydrator {
    fn rehydrate(
        &self,
        prior: Option<ScrpContext>,
        normalized: &NormalizedMessage,
    ) -> ScrpContext;
}