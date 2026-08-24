/**
 * Alioth 确定性校验 skill —— Node.js 客户端
 *
 * call-node.js：无需额外依赖，只用 Node 内置模块（https/fs/path）。
 * 用于没有 Python 环境的客户端（推荐默认用 Node.js，因为零依赖）。
 *
 * 用法（异步，返回 Promise）：
 *   const { verify } = require('./call-node.js');
 *   verify('601012','隆基绿能','归母净利润','2024-12-31', -8592102400.42, 'akshare').then(r => console.log(r));
 */
const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');

const HERE = __dirname;
const CONFIG = JSON.parse(fs.readFileSync(path.join(HERE, 'mcp_config.json'), 'utf8'));
let API_KEY = CONFIG.api_key || '';
const BASE_URL = CONFIG.base_url || 'https://alioth-api.titanplus.cn';

function _writeKey(key) {
  API_KEY = key;
  const cfg = JSON.parse(fs.readFileSync(path.join(HERE, 'mcp_config.json'), 'utf8'));
  cfg.api_key = key;
  fs.writeFileSync(path.join(HERE, 'mcp_config.json'), JSON.stringify(cfg, null, 2), 'utf8');
}

function _post(pathname, payload) {
  const url = new URL(BASE_URL + pathname);
  const lib = url.protocol === 'https:' ? https : http;
  const body = JSON.stringify(payload || {});
  return new Promise((resolve, reject) => {
    const req = lib.request({
      hostname: url.hostname,
      port: url.port || (url.protocol === 'https:' ? 443 : 80),
      path: url.pathname,
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) },
    }, (res) => {
      let data = '';
      res.on('data', (c) => (data += c));
      res.on('end', () => { try { resolve(JSON.parse(data)); } catch (e) { reject(e); } });
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

/** 匿名注册（第一次使用自动调用，零输入）。成功后自动写回 key。 */
async function register_anonymous() {
  const r = await _post('/register/anonymous', {});
  if (r && r.ok) _writeKey(r.api_key);
  return r;
}

/** 实名注册（付费绑定时用）。成功后自动写回 key。 */
async function register(username, password) {
  const r = await _post('/register', { username, password });
  if (r && r.ok) _writeKey(r.api_key);
  return r;
}

/** 校验一个财务指标是否正确。第一次使用自动匿名注册。 */
async function verify(company_code, company_name, metric_name, report_period, reported_value, source_name) {
  if (!API_KEY || API_KEY === 'your-alioth-key') {
    const reg = await register_anonymous();
    if (!reg || !reg.ok) {
      return { ok: false, error_code: 'register_required', error: '匿名注册失败，请手动 register(username, password)' };
    }
  }
  return _post('/verify_metric', {
    api_key: API_KEY, company_code, company_name, metric_name,
    report_period, reported_value, source_name,
  });
}

module.exports = { verify, register, register_anonymous };
