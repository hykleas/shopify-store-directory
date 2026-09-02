-- 006_ct_log_state.sql — CT log okuma imleci.
--
-- certstream.calidog.io public sunucusu olu oldugu icin CT loglarini dogrudan
-- RFC 6962 HTTP API'siyle okuyoruz. Her log icin nereye kadar geldigimizi
-- burada tutuyoruz ki yeniden baslatmada bastan taramayalim.

CREATE TABLE IF NOT EXISTS ct_log_state (
  log_url     TEXT PRIMARY KEY,
  next_index  BIGINT NOT NULL DEFAULT 0,
  tree_size   BIGINT,
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
