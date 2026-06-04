use tokio::io::{AsyncReadExt, AsyncWriteExt};
use crate::frame::Frame;

pub async fn read_frame<R: AsyncReadExt + Unpin>(r: &mut R) -> tokio::io::Result<Option<Frame>> {
    let mut len_buf = [0u8; 4];
    if let Err(e) = r.read_exact(&mut len_buf).await {
        if e.kind() == std::io::ErrorKind::UnexpectedEof {
            return Ok(None);
        }
        return Err(e);
    }
    let len = u32::from_be_bytes(len_buf) as usize;
    let mut buf = vec![0u8; len];
    r.read_exact(&mut buf).await?;
    let frame: Frame = bincode::deserialize(&buf)
        .map_err(|e| tokio::io::Error::new(std::io::ErrorKind::InvalidData, e))?;
    Ok(Some(frame))
}

pub async fn write_frame<W: AsyncWriteExt + Unpin>(w: &mut W, frame: &Frame) -> tokio::io::Result<()> {
    let bytes = bincode::serialize(frame)
        .map_err(|e| tokio::io::Error::new(std::io::ErrorKind::InvalidData, e))?;
    let len = (bytes.len() as u32).to_be_bytes();
    w.write_all(&len).await?;
    w.write_all(&bytes).await?;
    w.flush().await
}