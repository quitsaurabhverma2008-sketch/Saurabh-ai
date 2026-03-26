/* ═══════════════════════════════════════
   SAURABH AI - MEMORY SYSTEM v2.0
   Intelligent Memory with Cross-Chat Recall
══════════════════════════════════════ */

const MEMORY_KEY = 'sai7_memory';
const PROFILE_KEY = 'sai7_profile';

const DEFAULT_MEMORY = {
  profile: { name: '', occupation: '' },
  importantTopics: [],
  recentQueries: []
};

function loadMemory() {
  try {
    const saved = localStorage.getItem(MEMORY_KEY);
    if (saved) return JSON.parse(saved);
  } catch(e) {}
  return {...DEFAULT_MEMORY};
}

function saveMemory() {
  try {
    localStorage.setItem(MEMORY_KEY, JSON.stringify(memory));
  } catch(e) {}
}

let memory = loadMemory();

function initMemory() {
  memory = loadMemory();
  updateMemorySummary();
}

const IMPORTANT_KEYWORDS = [
  'project', 'portfolio', 'website', 'app', 'business', 'startup', 'company',
  'coding', 'programming', 'development', 'github', 'repo',
  'exam', 'college', 'iit', 'university', 'placement', 'interview',
  'job', 'career', 'internship', 'resume', 'cv',
  'goal', 'plan', 'dream', 'future', 'learning', 'teaching', 'help with',
  'family', 'health', 'hobby', 'passion', 'skill'
];

const UNIMPORTANT_PATTERNS = [
  /what'?s?\s*(the\s*)?(weather|time|date|today)/i,
  /how are you/i, /bye|goodbye/i, /^hi$|^hey$|^hello$/i,
  /^ok$|^yes$|^no$/i, /^thanks?$/i
];

function isImportantQuery(query) {
  const q = query.toLowerCase();
  for (const pattern of UNIMPORTANT_PATTERNS) {
    if (pattern.test(q)) return false;
  }
  for (const keyword of IMPORTANT_KEYWORDS) {
    if (q.includes(keyword)) return true;
  }
  if (query.length > 50) return true;
  if (/\b(how|what|why|explain|tell me|describe|help|make|create|build|write|code)\b/i.test(q)) return true;
  return false;
}

function extractTopicSummary(query) {
  let summary = query.substring(0, 60);
  if (query.length > 60) summary += '...';
  return summary;
}

function saveToMemory(query, topicSummary) {
  const chatId = AppState.chatId || 'general';
  const exists = memory.importantTopics.some(t => t.topic.toLowerCase() === topicSummary.toLowerCase());
  if (!exists) {
    memory.importantTopics.push({ topic: topicSummary, query: query, timestamp: Date.now(), chatId: chatId });
    if (memory.importantTopics.length > 50) memory.importantTopics = memory.importantTopics.slice(-50);
    saveMemory();
  }
}

const RECALL_PATTERNS = [
  /kya.*poocha.*(th?a|hai)/i, /kal.*kya.*poocha/i, /pehle.*kya.*poocha/i,
  /subah.*kya.*poocha/i, /raat.*kya.*poocha/i, /phle.*kya.*bola/i,
  /maine.*kya.*poocha.*tha/i, /kis.*baare.*mein.*baat.*ki/i,
  /what.*(did i|you).*(ask|ask?ed).*(before|earlier|yesterday|last)/i,
  /what.*was.*(my|our).*(question|query|topic)/i,
  /do you remember.*(my|i).*(question|query|topic)/i,
  /what.*were.*we.*(talking|discussing).*(about|earlier)/i,
  /earlier.*(question|topic|chat)/i, /previous.*(question|topic|chat)/i
];

function isRecallQuery(query) {
  for (const pattern of RECALL_PATTERNS) {
    if (pattern.test(query)) return true;
  }
  return false;
}

function getRecallContext(query) {
  const q = query.toLowerCase();
  let context = '';
  const topics = [...memory.importantTopics].sort((a, b) => b.timestamp - a.timestamp);
  if (topics.length === 0) return '';
  context = '\n\n===== PREVIOUS IMPORTANT TOPICS =====\n';
  const recentTopics = topics.slice(0, 5);
  recentTopics.forEach((t, i) => {
    const timeAgo = getTimeAgo(t.timestamp);
    context += `${i + 1}. [${timeAgo}] ${t.topic}
`;
  });
  if (/subah|morning/i.test(q)) {
    const morningTopics = topics.filter(t => { const hour = new Date(t.timestamp).getHours(); return hour >= 5 && hour < 12; });
    if (morningTopics.length > 0) {
      context = '\n\n===== MORNING TOPICS =====\n';
      morningTopics.forEach((t, i) => { context += `${i + 1}. ${t.topic}
`; });
    }
  }
  if (/raat|night|evening/i.test(q)) {
    const nightTopics = topics.filter(t => { const hour = new Date(t.timestamp).getHours(); return hour >= 18 && hour < 24; });
    if (nightTopics.length > 0) {
      context = '\n\n===== EVENING TOPICS =====\n';
      nightTopics.forEach((t, i) => { context += `${i + 1}. ${t.topic}
`; });
    }
  }
  context += '===== END PREVIOUS TOPICS =====\n';
  return context;
}

function getTimeAgo(timestamp) {
  const diff = Date.now() - timestamp;
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  if (minutes < 1) return 'abhi';
  if (minutes < 60) return `${minutes} min ago`;
  if (hours < 24) return `${hours} hours ago`;
  if (days === 1) return 'kal';
  if (days < 7) return `${days} din pehle`;
  return `${days} din pehle`;
}

const USER_INFO_PATTERNS = {
  name: [/my name is (\w+)/i, /i am (\w+)/i, /i'? ?m (\w+)/i, /mera naam (\w+) hai/i, /main (\w+) hoon/i],
  occupation: [/i am a (student|worker|developer|engineer|teacher|doctor|designer|freelancer|entrepreneur|businessman|businesswoman)/i, /i'? ?m a (student|worker|developer|engineer|teacher|doctor|designer|freelancer|entrepreneur|businessman|businesswoman)/i, /main (student|worker|developer|engineer|teacher|doctor|designer|freelancer|entrepreneur|businessman|businesswoman) hoon/i, /mein (student|worker|developer|engineer|teacher|doctor|designer|freelancer|entrepreneur|businessman|businesswoman) hoon/i]
};

function extractUserInfo(message) {
  const msg = message.toLowerCase();
  let updated = false;
  for (const pattern of USER_INFO_PATTERNS.occupation) {
    const match = msg.match(pattern);
    if (match) { if (memory.profile.occupation !== match[1].toLowerCase()) { memory.profile.occupation = match[1].toLowerCase(); updated = true; } break; }
  }
  for (const pattern of USER_INFO_PATTERNS.name) {
    const match = msg.match(pattern);
    if (match) { if (memory.profile.name !== match[1]) { memory.profile.name = match[1]; updated = true; } break; }
  }
  if (updated) { saveMemory(); updateMemorySummary(); }
}

function getMemoryContext(query) {
  let context = '';
  if (isRecallQuery(query)) context += getRecallContext(query);
  if (memory.profile.name || memory.profile.occupation) {
    context += '\n\n===== USER PROFILE =====\n';
    if (memory.profile.name) context += `Name: ${memory.profile.name}
`;
    if (memory.profile.occupation) context += `Occupation: ${memory.profile.occupation}
`;
    context += '===== END USER PROFILE =====\n';
  }
  return context;
}

function processAfterResponse(userQuery) {
  extractUserInfo(userQuery);
  if (isImportantQuery(userQuery)) saveToMemory(userQuery, extractTopicSummary(userQuery));
  memory.recentQueries.push({ query: userQuery, topic: extractTopicSummary(userQuery), timestamp: Date.now() });
  if (memory.recentQueries.length > 100) memory.recentQueries = memory.recentQueries.slice(-100);
  saveMemory();
}

function updateMemorySummary() {
  const el = document.getElementById('memoryTopicsSummary');
  if (el) {
    const count = memory.importantTopics.length;
    el.textContent = count > 0 ? `${count} topic${count > 1 ? 's' : ''} remembered` : 'No topics saved yet';
  }
}

initMemory();


function clearMemory() {
  if (confirm("Clear all remembered topics? This cannot be undone.")) {
    memory = {...DEFAULT_MEMORY, profile: memory.profile};
    saveMemory();
    updateMemorySummary();
    showToast("Memory cleared!");
  }
}

