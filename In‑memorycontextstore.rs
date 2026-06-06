pub struct InMemoryContextStore {
    inner: HashMap<(SovereignId, ManifoldId), ScrpContext>,
}

impl InMemoryContextStore {
    pub fn new() -> Self {
        Self { inner: HashMap::new() }
    }
}

impl ScrpContextStore for InMemoryContextStore {
    fn load_last(
        &self,
        sovereign: &SovereignId,
        manifold: &ManifoldId,
    ) -> Option<ScrpContext> {
        self.inner.get(&(sovereign.clone(), manifold.clone())).cloned()
    }

    fn save(&mut self, context: ScrpContext) {
        let key = (context.sovereign.clone(), context.manifold.clone());
        self.inner.insert(key, context);
    }
}