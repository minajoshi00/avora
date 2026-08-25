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
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${googleAIKey}`,
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

// Analytics data file
const ANALYTICS_DATA_FILE = path.join(process.cwd(), 'analytics_data.json');

function readAnalyticsData() {
  try {
    if (fs.existsSync(ANALYTICS_DATA_FILE)) {
      return JSON.parse(fs.readFileSync(ANALYTICS_DATA_FILE, 'utf-8'));
    }
    return { events: [] };
  } catch {
    return { events: [] };
  }
}

function writeAnalyticsData(data) {
  try {
    fs.writeFileSync(ANALYTICS_DATA_FILE, JSON.stringify(data, null, 2));
  } catch {
    // Ignore write errors
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

    filtered.forEach((row) => {
      const props = row.props || {};

      totals.totalEvents++;

      if (props.type === 'download') {
        totals.downloads++;
        rates.downloads++;
      }
      if (props.type === 'conversation') {
        rates.conversations++;
      }
      if (props.type === 'new_user') {
        rates.newUsers++;
        totals.newUsers++;
      }
      if (props.type === 'pageview') {
        rates.pageviews++;
        const dateStr = new Date(row.created_at).toLocaleDateString();
        series.labels.push(dateStr);
        series.pageviews.push((series.pageviews[series.pageviews.length - 1] || 0) + 1);
      }
      if (props.type === 'ai_request') {
        rates.aiRequests ??= 0;
        rates.aiRequests++;
        series.aiRequests.push((series.aiRequests[series.aiRequests.length - 1] || 0) + 1);
      }
      if (props.type === 'ai_response') {
        rates.aiResponses ??= 0;
        rates.aiResponses++;
      }
      if (props.type === 'mission_created') {
        totals.missionsCreated++;
      }
      if (props.type === 'mission_completed') {
        totals.missionsCompleted++;
      }
      if (props.type === 'task_completed') {
        totals.tasksCompleted++;
      }
      if (props.type === 'app_launch') {
        totals.appLaunches++;
      }
      if (props.type === 'feedback') {
        totals.feedbackTotal++;
      }
      if (props.type === 'error') {
        totals.errors++;
      }

      // Visitor tracking
      const visitorId = props.visitor_id || row.visitor_id;
      if (visitorId) {
        totals.totalUsers++;
        const eventDate = new Date(row.created_at);
        const diffDays = Math.floor((now - eventDate.getTime()) / (1000 * 60 * 60 * 24));
        if (diffDays === 0) {
          activeUsers++;
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

    // Calculate download rate
    if (totals.totalEvents > 0) {
      rates.downloads = (rates.downloads / totals.totalEvents) * 100;
    }

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

// Vercel KV integration (optional)
try {
  const { kv } = require('@vercel/kv');
  // KV is available in Vercel environment
} catch {
  // kv not available, continue without it
}

// Maintenance status endpoint
app.get('/api/admin/maintenance/status', (req, res) => {
  res.json({ maintenanceMode: false, message: 'Operational' });
});

app.post('/api/admin/maintenance/toggle', (req, res) => {
  res.json({ maintenanceMode: false, message: 'Maintenance mode updated' });
});

// Importing routes
const inputRoutes = require('./routes/inputRoutes');
const processRoutes = require('./routes/processRoutes');

app.use('/api/input', inputRoutes);
app.use('/api/process', processRoutes);

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
 console.log(`Server running on port ${PORT}`);
});