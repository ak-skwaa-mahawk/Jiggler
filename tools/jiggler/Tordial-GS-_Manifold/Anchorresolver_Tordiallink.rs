pub struct StaticAnchorResolver;

impl ScrpAnchorResolver for StaticAnchorResolver {
    fn resolve_anchor(&self, raw: &str) -> Option<ScrpAnchor> {
        if raw.contains("Tordial-GS-_Manifold") {
            Some(ScrpAnchor {
                raw: raw.to_string(),
                manifold: ManifoldId("Tordial-GS".into()),
            })
        } else {
            None
        }
    }
}