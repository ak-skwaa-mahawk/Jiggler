use std::sync::Arc;
use tokio::net::{TcpListener, TcpStream};
use tokio::task;

use crate::{
    backend::AgentNode,
    identity::{Sigma, AuthProvider},
    frame::Frame,
};
use crate::net::{read_frame, write_frame};

pub async fn run_tcp_mesh_listener(
    bind_addr: &str,
    sigma: Sigma,
    backend: Arc<dyn crate::backend::SovereignAgentBackend>,
    auth: Arc<dyn AuthProvider>,
) -> tokio::io::Result<()> {
    let listener = TcpListener::bind(bind_addr).await?;
    println!("sovereign node listening on {}", bind_addr);

    loop {
        let (socket, _peer) = listener.accept().await?;
        let sigma = sigma;
        let backend = backend.clone();
        let auth = auth.clone();

        task::spawn(async move {
            if let Err(e) = handle_tcp_connection(socket, sigma, backend, auth).await {
                eprintln!("connection error: {e}");
            }
        });
    }
}

async fn handle_tcp_connection(
    mut stream: TcpStream,
    sigma: Sigma,
    backend: Arc<dyn crate::backend::SovereignAgentBackend>,
    auth: Arc<dyn AuthProvider>,
) -> tokio::io::Result<()> {
    use std::collections::HashMap;
    use crate::sct::SovereignCapabilityToken;

    let mut node = AgentNode {
        sigma,
        backend: backend.as_ref(),
        auth: auth.as_ref(),
        sct_registry: HashMap::<[u8; 32], SovereignCapabilityToken>::new(),
    };

    loop {
        let maybe_frame: Option<Frame> = read_frame(&mut stream).await?;
        let Some(frame) = maybe_frame else {
            // EOF
            break;
        };

        if let Some(resp) = node.handle_frame(frame) {
            write_frame(&mut stream, &resp).await?;
        }
    }

    Ok(())
}