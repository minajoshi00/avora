try { require('dotenv').config(); } catch (_) {}
const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const helmet = require('helmet');
const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');

const app = express();

app.use(helmet());
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Google Generative AI endpoint
const googleAIKey = process.env.GEMINI_API_KEY;
const geminiModel = process.env.GEMINI_MODEL || 'gemini-2.5-flash';

app.get('/api/ai/gemini/health', (req, res) => {
  if (googleAIKey) {
    res.json({ status: 'ok', message: 'AI endpoint configured' });
  } else {
    res.status(503).json({ status: 'unavailable', message: 'AI service not configured' });
  }
});

app.post('/api/ai/gemini', async (req, res) => {
  try {
    const { prompt } = req.body;
    if (!prompt) {
      return res.status(400).json({ error: 'Prompt is required' });
    }

    if (!googleAIKey) {
      return res.status(503).json({ error: 'AI service not configured. Set GEMINI_API_KEY.' });
    }

    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/${geminiModel}:generateContent?key=${googleAIKey}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          contents: [{ role: 'user', parts: [{ text: prompt }] }],
        }),
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      return res.status(response.status).json({ error: errorData.error || 'AI service failed' });
    }

    const data = await response.json();
    const text = data.candidates?.[0]?.content?.parts?.[0]?.text || 'No response from AI';

    res.json({ response: text });
  } catch (error) {
    console.error('AI Gemini error:', error);
    res.status(500).json({ error: error.message || 'AI processing failed' });
  }
});

// AI chat endpoint with Gemini + Groq fallback
// NEVER exposes API keys to the frontend - all processing is server-side
app.post('/api/ai/chat', async (req, res) => {
  try {
    const { prompt } = req.body;
    if (!prompt) {
      return res.status(400).json({ error: 'Prompt is required' });
    }

    // Try Gemini first
    if (googleAIKey) {
      try {
        const geminiCtrl = new AbortController();
        const geminiTimeout = setTimeout(() => geminiCtrl.abort(), 15000);
        const geminiResponse = await fetch(
          `https://generativelanguage.googleapis.com/v1beta/models/${geminiModel}:generateContent?key=${googleAIKey}`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              contents: [{ role: 'user', parts: [{ text: prompt }] }],
            }),
            signal: geminiCtrl.signal,
          }
        );
        clearTimeout(geminiTimeout);

        if (geminiResponse.ok) {
          const data = await geminiResponse.json();
          const text = data.candidates?.[0]?.content?.parts?.[0]?.text || 'No response from AI';
          res.json({ response: text, provider: 'gemini' });
          return;
        } else {
          const errBody = await geminiResponse.text().catch(() => '');
          console.warn(`Gemini returned ${geminiResponse.status}: ${errBody.slice(0, 300)}`);
        }
      } catch (geminiError) {
        console.warn('Gemini AI failed, falling back to Groq:', geminiError.message);
      }
    }

    // Fallback to Groq
    const groqKey = process.env.GROQ_API_KEY;
    const groqModel = process.env.GROQ_MODEL || 'openai/gpt-oss-120b';
    if (groqKey) {
      try {
        const groqCtrl = new AbortController();
        const groqTimeout = setTimeout(() => groqCtrl.abort(), 15000);
        const groqResponse = await fetch('https://api.groq.com/openai/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${groqKey}`,
          },
          body: JSON.stringify({
            model: groqModel,
            messages: [{ role: 'user', content: prompt }],
          }),
          signal: groqCtrl.signal,
        });
        clearTimeout(groqTimeout);

        if (groqResponse.ok) {
          const data = await groqResponse.json();
          const text = data.choices?.[0]?.message?.content || 'No response from AI';
          res.json({ response: text, provider: 'groq' });
          return;
        } else {
          const errBody = await groqResponse.text().catch(() => '');
          console.warn(`Groq returned ${groqResponse.status}: ${errBody.slice(0, 300)}`);
        }
      } catch (groqError) {
        console.warn('Groq AI fallback failed:', groqError.message);
      }
    }

    // Both providers failed
    res.status(503).json({ error: 'AI service unavailable. All providers failed.' });
  } catch (error) {
    console.error('AI chat error:', error);
    res.status(500).json({ error: error.message || 'AI processing failed' });
  }
});

// Analytics data file
const ANALYTICS_DATA_FILE = path.join(process.cwd(), '..', 'analytics_data.json');

function readAnalyticsData() {
  try {
    if (fs.existsSync(ANALYTICS_DATA_FILE)) {
      return JSON.parse(fs.readFileSync(ANALYTICS_DATA_FILE, 'utf-8'));
    }
    return { events: [] };
  } catch (err) {
    console.warn('readAnalyticsData failed:', err.message);
    return { events: [] };
  }
}

function writeAnalyticsData(data) {
  try {
    fs.writeFileSync(ANALYTICS_DATA_FILE, JSON.stringify(data, null, 2));
  } catch (err) {
    console.warn('writeAnalyticsData failed:', err.message);
  }
}

// API: Track an analytics event
app.post('/api/analytics/events', (req, res) => {
  try {
    const { event_type, props, visitor_id } = req.body;
    if (!event_type) {
      return res.status(400).json({ error: 'event_type is required' });
    }

    const data = readAnalyticsData();
    const event = {
      id: uuidv4(),
      event_type,
      props: props || {},
      visitor_id: visitor_id || `visitor_${Date.now()}_${uuidv4().slice(0, 8)}`,
      created_at: new Date().toISOString(),
    };

    data.events.push(event);
    writeAnalyticsData(data);

    res.json({ success: true, inserted: true });
  } catch (error) {
    console.error('Analytics event error:', error);
    res.status(500).json({ error: error.message || 'Failed to store event' });
  }
});

// API: Get analytics summary
app.get('/api/analytics/summary', (req, res) => {
  try {
    const range = req.query.range || '7d';
    const data = readAnalyticsData();
    const events = data.events || [];
    const now = new Date().getTime();

    // Filter events by range
    let filtered = events;
    if (range === '24h') {
      filtered = events.filter((e) => new Date(e.created_at).getTime() >= now - 24 * 60 * 60 * 1000);
    } else if (range === '7d') {
      filtered = events.filter((e) => new Date(e.created_at).getTime() >= now - 7 * 24 * 60 * 60 * 1000);
    } else if (range === '30d') {
      filtered = events.filter((e) => new Date(e.created_at).getTime() >= now - 30 * 24 * 60 * 60 * 1000);
    } else if (range === '90d') {
      filtered = events.filter((e) => new Date(e.created_at).getTime() >= now - 90 * 24 * 60 * 60 * 1000);
    }

    // Aggregate data
    const totals = {
      totalEvents: filtered.length,
      totalUsers: 0,
      activeUsers: 0,
      newUsers: 0,
      returningUsers: 0,
      totalConversations: 0,
      messagesSent: 0,
      aiRequests: 0,
      aiResponses: 0,
      missionsCreated: 0,
      missionsCompleted: 0,
      tasksCompleted: 0,
      downloads: 0,
      appLaunches: 0,
      errors: 0,
      feedbackTotal: 0,
    };

    const rates = {
      downloads: 0,
      conversations: 0,
      newUsers: 0,
      pageviews: 0,
    };

    const breakdowns = {
      countries: [],
      platforms: [],
      providers: [],
    };

    const series = {
      labels: [],
      pageviews: [],
      downloads: [],
      conversations: [],
      aiRequests: [],
    };

    const yearMap = {};
    const distinctVisitors = new Set();
    const activeVisitors = new Set();
    let rawDownloadCount = 0;

    filtered.forEach((row) => {
      const props = row.props || {};
      const eventType = props.type || row.event_type;

      if (eventType === 'download') {
        totals.downloads++;
        rawDownloadCount++;
      }
      if (eventType === 'conversation') {
        totals.totalConversations++;
        totals.messagesSent++;
        rates.conversations++;
      }
      if (eventType === 'message') {
        totals.messagesSent++;
      }
      if (eventType === 'new_user') {
        rates.newUsers++;
        totals.newUsers++;
      }
      if (eventType === 'pageview') {
        rates.pageviews++;
        const dateStr = new Date(row.created_at).toLocaleDateString();
        series.labels.push(dateStr);
        series.pageviews.push((series.pageviews[series.pageviews.length - 1] || 0) + 1);
      }
      if (eventType === 'ai_request') {
        totals.aiRequests++;
        rates.aiRequests = (rates.aiRequests || 0) + 1;
        series.aiRequests.push((series.aiRequests[series.aiRequests.length - 1] || 0) + 1);
      }
      if (eventType === 'ai_response') {
        totals.aiResponses++;
        rates.aiResponses = (rates.aiResponses || 0) + 1;
      }
      if (eventType === 'mission_created') {
        totals.missionsCreated++;
      }
      if (eventType === 'mission_completed') {
        totals.missionsCompleted++;
      }
      if (eventType === 'task_completed') {
        totals.tasksCompleted++;
      }
      if (eventType === 'app_launch') {
        totals.appLaunches++;
      }
      if (eventType === 'feedback') {
        totals.feedbackTotal++;
      }
      if (eventType === 'error') {
        totals.errors++;
      }

      // Distinct visitor tracking
      const visitorId = props.visitor_id || row.visitor_id;
      if (visitorId) {
        distinctVisitors.add(String(visitorId));
        const eventDate = new Date(row.created_at);
        const diffDays = Math.floor((now - eventDate.getTime()) / (1000 * 60 * 60 * 24));
        if (diffDays === 0) {
          activeVisitors.add(String(visitorId));
        }
        const yearKey = eventDate.getFullYear();
        if (!yearMap[yearKey]) yearMap[yearKey] = 0;
        yearMap[yearKey]++;
      }

      // Breakdowns
      if (props.platform) {
        const platformName = props.platform;
        const existing = breakdowns.platforms.find((p) => p.name === platformName);
        if (existing) {
          existing.count++;
        } else {
          breakdowns.platforms.push({ name: platformName, count: 1 });
        }
      }

      if (props.country) {
        const countryName = props.country;
        const existing = breakdowns.countries.find((c) => c.name === countryName);
        if (existing) {
          existing.count++;
        } else {
          breakdowns.countries.push({ name: countryName, count: 1 });
        }
      }

      if (props.provider) {
        const providerName = props.provider;
        const existing = breakdowns.providers.find((p) => p.name === providerName);
        if (existing) {
          existing.count++;
        } else {
          breakdowns.providers.push({ name: providerName, count: 1 });
        }
      }
    });

    totals.totalUsers = distinctVisitors.size;
    totals.activeUsers = activeVisitors.size;
    totals.returningUsers = Math.max(0, totals.totalUsers - totals.newUsers);
    // Calculate download rate as percentage
    if (totals.totalEvents > 0) {
      rates.downloads = (rawDownloadCount / totals.totalEvents) * 100;
    }
    // Compute percentages for breakdowns
    function withPercent(arr) {
      const total = arr.reduce((s, x) => s + x.count, 0) || 1;
      return arr.map(x => ({ ...x, percentage: Math.round((x.count / total) * 1000) / 10 }));
    }
    breakdowns.countries = withPercent(breakdowns.countries).sort((a,b)=> b.count - a.count);
    breakdowns.platforms = withPercent(breakdowns.platforms).sort((a,b)=> b.count - a.count);
    breakdowns.providers = withPercent(breakdowns.providers).sort((a,b)=> b.count - a.count);

    const summary = {
      range,
      generatedAt: new Date().toISOString(),
      hasData: totals.totalEvents > 0,
      totals,
      rates,
      breakdowns,
      series,
    };

    res.json(summary);
  } catch (error) {
    console.error('Analytics summary error:', error);
    res.status(500).json({ error: error.message || 'Failed to fetch analytics summary' });
  }
});

// Real health endpoint — returns live process + analytics file stats, no fake values
app.get('/api/health', (req, res) => {
  try {
    const os = require('os');
    const uptimeSec = process.uptime();
    const mem = process.memoryUsage();
    let analyticsBytes = null;
    let analyticsEvents = null;
    try {
      if (fs.existsSync(ANALYTICS_DATA_FILE)) {
        const stat = fs.statSync(ANALYTICS_DATA_FILE);
        analyticsBytes = stat.size;
        const raw = JSON.parse(fs.readFileSync(ANALYTICS_DATA_FILE, 'utf-8'));
        analyticsEvents = Array.isArray(raw.events) ? raw.events.length : null;
      }
    } catch (_) {}
    res.json({
      status: 'ok',
      uptimeSec: Math.floor(uptimeSec),
      uptimeHuman: `${Math.floor(uptimeSec/3600)}h ${Math.floor((uptimeSec%3600)/60)}m`,
      memory: {
        rssMB: Math.round(mem.rss / 1024 / 1024 * 10)/10,
        heapUsedMB: Math.round(mem.heapUsed / 1024 / 1024 * 10)/10,
        heapTotalMB: Math.round(mem.heapTotal / 1024 / 1024 * 10)/10,
        systemTotalMB: Math.round(os.totalmem()/1024/1024),
        systemFreeMB: Math.round(os.freemem()/1024/1024),
      },
      cpu: { count: os.cpus().length, model: os.cpus()[0]?.model || 'unknown', loadAvg: os.loadavg() },
      platform: os.platform(),
      node: process.version,
      analytics: analyticsBytes !== null ? { bytes: analyticsBytes, events: analyticsEvents, path: path.basename(ANALYTICS_DATA_FILE) } : { bytes: null, events: null, note: 'no analytics file yet' },
      ai: { geminiConfigured: !!process.env.GEMINI_API_KEY, groqConfigured: !!process.env.GROQ_API_KEY, geminiModel: geminiModel, groqModel: process.env.GROQ_MODEL || 'openai/gpt-oss-120b' },
      maintenanceMode: readMaintenanceMode(),
    });
  } catch (e) {
    res.status(500).json({ status: 'error', error: e.message });
  }
});

// Vercel KV integration removed - not used in this service (analytics uses file JSON)

// Importing routes
const inputRoutes = require('./routes/inputRoutes');
const processRoutes = require('./routes/processRoutes');

app.use('/api/input', inputRoutes);
app.use('/api/process', processRoutes);

const PORT = process.env.PORT || 3000;

// Maintenance mode persistence file
const MAINTENANCE_FILE = path.join(process.cwd(), 'maintenance.json');

function readMaintenanceMode() {
  try {
    if (fs.existsSync(MAINTENANCE_FILE)) {
      const data = JSON.parse(fs.readFileSync(MAINTENANCE_FILE, 'utf-8'));
      return data.maintenanceMode === true || data.maintenanceMode === 'true';
    }
  } catch (err) {
    console.warn('readMaintenanceMode failed:', err.message);
  }
  return false;
}

function writeMaintenanceMode(mode) {
  try {
    fs.writeFileSync(MAINTENANCE_FILE, JSON.stringify({ maintenanceMode: mode }, null, 2));
  } catch (err) {
    console.warn('writeMaintenanceMode failed:', err.message);
  }
}

// Maintenance status endpoint
app.get('/api/admin/maintenance/status', (req, res) => {
  res.json({ maintenanceMode: readMaintenanceMode() });
});

app.post('/api/admin/maintenance/toggle', (req, res) => {
  const { password } = req.body;
  const expectedPassword = process.env.MAINTENANCE_ADMIN_PASSWORD;
  if (!expectedPassword) {
    console.error('MAINTENANCE_ADMIN_PASSWORD not set - refusing toggle');
    return res.status(503).json({ error: 'Maintenance toggle not configured on server.' });
  }
  
  if (!password || password !== expectedPassword) {
    return res.status(401).json({ error: 'Unauthorized. Invalid admin password.' });
  }
  
  const newMode = !readMaintenanceMode();
  writeMaintenanceMode(newMode);
  res.json({ maintenanceMode: newMode, message: newMode ? 'Maintenance mode enabled' : 'Maintenance mode disabled' });
});

app.listen(PORT, () => {
 console.log(`Server running on port ${PORT}`);
});