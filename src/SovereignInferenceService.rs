#[derive(Debug)]
pub struct SovereignInferenceService {
    conn: Connection,
}

impl SovereignInferenceService {
    pub fn new(conn: Connection) -> Self {
        Self { conn }
    }

    #[inline]
    fn living_toroidal_pi_r() -> f32 {
        3.267_253_6
    }
}

#[tonic::async_trait]
impl InferenceService for SovereignInferenceService {

    // === Existing methods (EncodeRadHardGlyph, RunClientlessPulse, etc.) stay the same ===

    // =====================================================
    // NEW: Intent Engine Read Methods
    // =====================================================

    async fn get_intent_band(
        &self,
        request: Request<GetIntentBandRequest>,
    ) -> Result<Response<GrpcIntentBand>, Status> {
        let req = request.into_inner();

        let result = self.conn.query_row(
            "SELECT intent_value, lastupdatets, source 
             FROM intent_band 
             WHERE id = ?1 AND mode = ?2",
            params![req.band_id, req.mode],
            |row| {
                Ok(GrpcIntentBand {
                    band_id: req.band_id.clone(),
                    mode: req.mode,
                    intent_value: row.get(0)?,
                    last_updated: row.get(1)?,
                    source: row.get(2)?,
                })
            },
        );

        match result {
            Ok(band) => Ok(Response::new(band)),
            Err(rusqlite::Error::QueryReturnedNoRows) => {
                Err(Status::not_found(format!(
                    "Intent band '{}' (mode {}) not found",
                    req.band_id, req.mode
                )))
            }
            Err(e) => Err(Status::internal(e.to_string())),
        }
    }

    async fn get_all_intent_bands(
        &self,
        _request: Request<()>,
    ) -> Result<Response<GetAllIntentBandsResponse>, Status> {
        let mut stmt = self.conn.prepare(
            "SELECT id, mode, intent_value, lastupdatets, source FROM intent_band"
        ).map_err(|e| Status::internal(e.to_string()))?;

        let bands = stmt
            .query_map([], |row| {
                Ok(GrpcIntentBand {
                    band_id: row.get(0)?,
                    mode: row.get(1)?,
                    intent_value: row.get(2)?,
                    last_updated: row.get(3)?,
                    source: row.get(4)?,
                })
            })
            .map_err(|e| Status::internal(e.to_string()))?
            .collect::<std::result::Result<Vec<_>, _>>()?;

        Ok(Response::new(GetAllIntentBandsResponse { bands }))
    }
}