"""
CHAFF Ghost Engine MVP — v0.1.0
================================
Generates synthetic Reddit personas with realistic behavioral patterns.
Each ghost is derived deterministically from a seed — no database needed.
Ghosts post, comment, and browse on realistic human schedules.

Platform: Reddit (Phase 1 only)
Requires: Python 3.10+, praw, ollama, schedule, faker

Install deps:
    pip install praw ollama schedule faker requests

Ollama (local LLM — free, runs on your machine):
    Download from https://ollama.com
    Then run: ollama pull mistral

Usage:
    python ghost_engine.py --seed abc123 --count 1 --dry-run

Author: Project CHAFF — github.com/MT25MB/chaff-extension
License: GPL-3.0
"""

import sys
import argparse
import hashlib
import json
import logging
import math
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional
try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False
    print("[WARN] schedule not installed. Run: pip install schedule")

# ── Optional imports (graceful degradation) ──────────────────────────────────
try:
    import praw
    PRAW_AVAILABLE = True
except ImportError:
    PRAW_AVAILABLE = False
    print("[WARN] praw not installed. Run: pip install praw")

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("[WARN] ollama not installed. Run: pip install ollama")

try:
    from faker import Faker
    FAKER_AVAILABLE = True
except ImportError:
    FAKER_AVAILABLE = False

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [CHAFF] %(levelname)s %(message)s',
    datefmt='%H:%M:%S',
    encoding='utf-8'
)
log = logging.getLogger('chaff')


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: DETERMINISTIC IDENTITY GENERATION
# Every ghost is fully derived from its seed. Given the same seed,
# any node in the network generates the identical ghost profile.
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PersonalityVector:
    """Big Five personality model — determines all behavioral patterns."""
    openness: float        # 0-1: curiosity, creativity, breadth of interests
    conscientiousness: float  # 0-1: organization, reliability, posting regularity
    extraversion: float    # 0-1: posting frequency, social engagement
    agreeableness: float   # 0-1: tone of posts, conflict avoidance
    neuroticism: float     # 0-1: emotional variability, rant frequency


@dataclass
class GhostProfile:
    """Complete synthetic identity. Fully deterministic from seed."""
    seed: str
    username: str
    age: int
    location_city: str
    location_state: str
    timezone_offset: int       # UTC offset, e.g. -5 for EST
    occupation: str
    education: str
    personality: PersonalityVector
    interests: list[str]       # subreddits this ghost frequents
    writing_style: dict        # vocabulary level, typo rate, emoji usage, etc.
    posting_schedule: dict     # peak hours, avg posts per day, gap distribution
    life_events: list[str]     # backstory fragments for contextual posting
    karma_target: int          # realistic karma range to grow toward
    created_date: datetime     # simulated account age


class GhostGenerator:
    """
    Generates GhostProfile instances deterministically from seeds.
    Same seed → same ghost, every time, on any machine.
    """

    CITIES = [
        ("Denver", "CO", -7), ("Austin", "TX", -6), ("Portland", "OR", -8),
        ("Nashville", "TN", -6), ("Columbus", "OH", -5), ("Raleigh", "NC", -5),
        ("Minneapolis", "MN", -6), ("Phoenix", "AZ", -7), ("Pittsburgh", "PA", -5),
        ("Salt Lake City", "UT", -7), ("Richmond", "VA", -5), ("Boise", "ID", -7),
        ("Louisville", "KY", -5), ("Oklahoma City", "OK", -6), ("Tucson", "AZ", -7),
        ("Albuquerque", "NM", -7), ("Omaha", "NE", -6), ("Tulsa", "OK", -6),
        ("Rochester", "NY", -5), ("Spokane", "WA", -8),
    ]

    OCCUPATIONS = [
        "software developer", "teacher", "nurse", "accountant", "graphic designer",
        "electrician", "project manager", "marketing coordinator", "librarian",
        "mechanic", "paralegal", "social worker", "lab technician", "chef",
        "physical therapist", "HR specialist", "data analyst", "photographer",
        "HVAC technician", "office manager", "freelance writer", "real estate agent",
    ]

    EDUCATIONS = [
        "high school diploma", "some college", "associate's degree",
        "bachelor's degree", "master's degree", "trade certification",
    ]

    # Curated subreddit list — general interest, not extremist or controversial
    INTEREST_POOLS = {
        "tech": ["programming", "sysadmin", "technology", "linux", "Python",
                 "MachineLearning", "homelab", "pcmasterrace", "cybersecurity"],
        "lifestyle": ["cooking", "running", "hiking", "gardening", "DIY",
                      "personalfinance", "frugal", "minimalism", "yoga"],
        "culture": ["books", "movies", "Music", "podcasts", "television",
                    "boardgames", "photography", "Art"],
        "local": ["news", "todayilearned", "worldnews", "science",
                  "askscience", "explainlikeimfive", "OutOfTheLoop"],
        "fun": ["funny", "mildlyinteresting", "Showerthoughts", "LifeProTips",
                "Unexpected", "interestingasfuck", "oddlysatisfying"],
        "animals": ["aww", "dogs", "cats", "whatsthisbird", "NatureIsFuckingLit"],
    }

    def __init__(self, seed: str):
        self.seed = seed
        self._h = self._make_hasher(seed)

    def _make_hasher(self, seed: str):
        """Returns a deterministic pseudo-random number generator."""
        base = hashlib.sha256(seed.encode()).digest()
        counter = [0]
        def h(n: int = 0) -> float:
            """Returns a float in [0,1), different each call."""
            data = base + counter[0].to_bytes(4, 'big') + n.to_bytes(4, 'big')
            counter[0] += 1
            digest = hashlib.sha256(data).digest()
            return int.from_bytes(digest[:4], 'big') / 0xFFFFFFFF
        return h

    def _pick(self, lst: list) -> any:
        idx = int(self._h() * len(lst))
        return lst[min(idx, len(lst) - 1)]

    def _int(self, lo: int, hi: int) -> int:
        return int(self._h() * (hi - lo + 1)) + lo

    def generate(self) -> GhostProfile:
        h = self._h

        # Demographics
        city, state, tz = self._pick(self.CITIES)
        age = self._int(19, 58)
        occupation = self._pick(self.OCCUPATIONS)
        education = self._pick(self.EDUCATIONS)

        # Username — realistic Reddit-style
        username = self._generate_username()

        # Personality (Big Five)
        personality = PersonalityVector(
            openness=h(),
            conscientiousness=h(),
            extraversion=h(),
            agreeableness=h(),
            neuroticism=h(),
        )

        # Interests — 4-8 subreddits, weighted by personality
        interests = self._generate_interests(personality)

        # Writing style
        writing_style = {
            "vocab_level": ["simple", "casual", "moderate", "articulate"][self._int(0, 3)],
            "typo_rate": h() * 0.04,        # 0-4% of words have a typo
            "emoji_rate": h() * 0.15,       # 0-15% of posts have emoji
            "avg_length_words": self._int(15, 120),
            "uses_punctuation": h() > 0.3,
            "capitalizes_sentences": h() > 0.2,
            "uses_ellipsis": h() > 0.6,
            "all_lowercase": h() > 0.7,
        }

        # Posting schedule — derived from personality + occupation
        posting_schedule = self._generate_schedule(personality, occupation, tz)

        # Life events — fragments for contextual authenticity
        life_events = self._generate_life_events(age, occupation, city)

        # Account age — ghosts should appear to have history
        days_old = self._int(60, 730)
        created_date = datetime.now() - timedelta(days=days_old)

        karma_target = self._int(200, 8000)

        return GhostProfile(
            seed=self.seed,
            username=username,
            age=age,
            location_city=city,
            location_state=state,
            timezone_offset=tz,
            occupation=occupation,
            education=education,
            personality=personality,
            interests=interests,
            writing_style=writing_style,
            posting_schedule=posting_schedule,
            life_events=life_events,
            karma_target=karma_target,
            created_date=created_date,
        )

    def _generate_username(self) -> str:
        """Generates a realistic Reddit username."""
        adjectives = ["quiet", "clever", "wandering", "sleepy", "golden",
                      "coastal", "winter", "emerald", "silver", "dusty",
                      "lazy", "swift", "hidden", "wild", "calm"]
        nouns = ["fox", "river", "pine", "stone", "hawk", "creek", "ridge",
                 "wolf", "oak", "jay", "deer", "fern", "brook", "trail", "peak"]
        patterns = [
            lambda: f"{self._pick(adjectives)}_{self._pick(nouns)}{self._int(10,999)}",
            lambda: f"{self._pick(nouns)}_{self._pick(adjectives)}",
            lambda: f"the_{self._pick(adjectives)}_{self._pick(nouns)}",
            lambda: f"{self._pick(adjectives)}{self._pick(nouns).capitalize()}",
        ]
        return self._pick(patterns)()

    def _generate_interests(self, p: PersonalityVector) -> list[str]:
        """Selects subreddits based on personality."""
        pool = list(self.INTEREST_POOLS["fun"]) + list(self.INTEREST_POOLS["local"])
        if p.openness > 0.6:
            pool += self.INTEREST_POOLS["culture"]
        if p.openness > 0.5:
            pool += self.INTEREST_POOLS["tech"]
        pool += self.INTEREST_POOLS["lifestyle"]
        if self._h() > 0.5:
            pool += self.INTEREST_POOLS["animals"]
        random.shuffle(pool)
        count = self._int(4, 9)
        return list(dict.fromkeys(pool))[:count]  # dedupe, preserve order

    def _generate_schedule(self, p: PersonalityVector, occ: str, tz: int) -> dict:
        """Generates realistic posting time distribution."""
        # Office workers post during lunch and evening
        # Extroverts post more frequently
        base_posts_per_day = 0.3 + p.extraversion * 2.5
        is_office = any(w in occ for w in ["developer", "accountant", "manager",
                                            "analyst", "coordinator", "specialist"])

        if is_office:
            peak_hours = [12, 13, 19, 20, 21]  # lunch + evening
        else:
            peak_hours = [9, 10, 14, 19, 20]   # mid-morning + evening

        return {
            "avg_posts_per_day": round(base_posts_per_day, 2),
            "peak_hours_utc": [(h - tz) % 24 for h in peak_hours],
            "weekend_multiplier": 1.3 + p.extraversion * 0.5,
            "silence_probability": 0.2 + p.conscientiousness * 0.1,
            # Probability ghost goes silent on any given day
            "binge_probability": p.neuroticism * 0.15,
            # Occasional high-activity bursts
        }

    def _generate_life_events(self, age: int, occ: str, city: str) -> list[str]:
        """Creates backstory fragments used for contextual posting."""
        events = [f"lives in {city}", f"works as a {occ}"]
        if age > 25:
            events.append("has been at current job for a few years")
        if age > 30:
            events.append("is thinking about buying a house")
        if self._h() > 0.5:
            events.append("has a dog")
        if self._h() > 0.6:
            events.append("recently started cooking more at home")
        if self._h() > 0.7:
            events.append("is trying to get more exercise")
        if self._h() > 0.8:
            events.append("is saving up for a trip")
        return events


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: CONTENT GENERATION (LOCAL LLM)
# Uses Ollama running locally — no API keys, no cloud, no logs.
# ─────────────────────────────────────────────────────────────────────────────

class ContentGenerator:
    """
    Generates realistic social media content using a local LLM.
    Falls back to template-based generation if Ollama is unavailable.
    """

    MODEL = "mistral"  # or "llama3", "gemma2" — any Ollama model

    def __init__(self, profile: GhostProfile, dry_run: bool = False):
        self.profile = profile
        self.dry_run = dry_run
        self.ollama_ok = OLLAMA_AVAILABLE and not dry_run
        if self.ollama_ok:
            try:
                ollama.list()  # test connection
                log.info(f"[{profile.username}] Ollama connected — using {self.MODEL}")
            except Exception:
                self.ollama_ok = False
                log.warning(f"[{profile.username}] Ollama not running — using templates")

    def _build_system_prompt(self) -> str:
        p = self.profile
        style = p.writing_style
        personality_desc = []
        if p.personality.extraversion > 0.7:
            personality_desc.append("chatty and social")
        elif p.personality.extraversion < 0.3:
            personality_desc.append("quiet and observational")
        if p.personality.agreeableness > 0.7:
            personality_desc.append("friendly and supportive")
        if p.personality.neuroticism > 0.7:
            personality_desc.append("occasionally anxious or stressed")
        if p.personality.openness > 0.7:
            personality_desc.append("curious and open-minded")

        return f"""You are a Reddit user named {p.username}. Write in first person as this person.

IDENTITY:
- Age: {p.age}, lives in {p.location_city}, {p.location_state}
- Works as: {p.occupation}
- Personality: {', '.join(personality_desc) or 'balanced and neutral'}
- Life context: {'; '.join(p.life_events)}

WRITING STYLE:
- Vocabulary level: {style['vocab_level']}
- {'Uses lowercase a lot' if style['all_lowercase'] else 'Capitalizes normally'}
- {'Often skips punctuation' if not style['uses_punctuation'] else 'Uses punctuation normally'}
- Average post length: {style['avg_length_words']} words
- Typo rate: {'occasional typos' if style['typo_rate'] > 0.02 else 'mostly clean'}

RULES:
- Never mention being an AI
- Stay in character completely
- Write naturally, not perfectly
- Match the vocabulary level specified
- Keep to the approximate word count
- Sound like a real, specific person — not generic"""

    def generate_comment(self, subreddit: str, post_title: str, post_body: str = "") -> str:
        """Generate a realistic comment on a post."""
        if not self.ollama_ok:
            return self._fallback_comment(subreddit)

        prompt = f"""Write a Reddit comment for this post in r/{subreddit}.

POST TITLE: {post_title}
POST BODY: {post_body[:300] if post_body else '(no body)'}

Write a natural comment as {self.profile.username}. 
Do not start with "I" — vary how you start.
Keep it under {self.profile.writing_style['avg_length_words']} words."""

        try:
            response = ollama.chat(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": self._build_system_prompt()},
                    {"role": "user", "content": prompt}
                ]
            )
            return response['message']['content'].strip()
        except Exception as e:
            log.error(f"Ollama error: {e}")
            return self._fallback_comment(subreddit)

    def generate_post(self, subreddit: str) -> tuple[str, str]:
        """Generate a post title and body for a subreddit. Returns (title, body)."""
        if not self.ollama_ok:
            return self._fallback_post(subreddit)

        prompt = f"""Write a Reddit post for r/{subreddit}.

Generate:
1. A natural post title (not clickbait, conversational)
2. A post body (can be short, 1-3 paragraphs max)

Format your response as:
TITLE: [title here]
BODY: [body here]

Keep the title under 100 characters. Keep the body under 200 words.
Make it something a real {self.profile.age}-year-old {self.profile.occupation} might actually post."""

        try:
            response = ollama.chat(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": self._build_system_prompt()},
                    {"role": "user", "content": prompt}
                ]
            )
            text = response['message']['content'].strip()
            lines = text.split('\n')
            title = next((l.replace('TITLE:', '').strip() for l in lines if l.startswith('TITLE:')), "")
            body_start = text.find('BODY:')
            body = text[body_start + 5:].strip() if body_start != -1 else ""
            return title, body
        except Exception as e:
            log.error(f"Ollama error: {e}")
            return self._fallback_post(subreddit)

    def _fallback_comment(self, subreddit: str) -> str:
        """Template-based fallback when Ollama is unavailable."""
        templates = [
            "This is really interesting, thanks for sharing.",
            "Good point. I've had a similar experience honestly.",
            "Hadn't thought about it that way before.",
            "Yeah this tracks with what I've seen too.",
            "Appreciate you posting this.",
            "Makes sense to me. Solid take.",
            "Been following this for a while, good to see it discussed here.",
        ]
        return random.choice(templates)

    def _fallback_post(self, subreddit: str) -> tuple[str, str]:
        titles = [
            f"Anyone else find this interesting?",
            f"Thoughts on this?",
            f"Been thinking about this lately",
            f"Question for r/{subreddit}",
            f"Sharing this because I found it helpful",
        ]
        bodies = [
            "Just something I've been thinking about lately. Curious what others think.",
            "Found this recently and thought it was worth sharing here.",
            "Not sure if this is the right place but figured I'd ask.",
        ]
        return random.choice(titles), random.choice(bodies)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: BEHAVIORAL SCHEDULER
# Decides WHEN a ghost posts based on their personality and schedule.
# This is what makes ghosts feel human — timing is everything.
# ─────────────────────────────────────────────────────────────────────────────

class BehaviorScheduler:
    """
    Determines whether and when a ghost should take an action.
    Models human circadian rhythms, attention patterns, and life events.
    """

    def __init__(self, profile: GhostProfile):
        self.profile = profile
        self.schedule = profile.posting_schedule
        self._action_queue = []

    def should_post_now(self) -> bool:
        """Returns True if the ghost should post in the current hour."""
        now_utc = datetime.now(timezone.utc)
        hour = now_utc.hour
        dow = now_utc.weekday()  # 0=Monday

        # Silence day check
        if random.random() < self.schedule['silence_probability']:
            return False

        # Check if we're in a peak hour
        in_peak = hour in self.schedule['peak_hours_utc']
        base_prob = self.schedule['avg_posts_per_day'] / 24

        # Weekend boost
        if dow >= 5:
            base_prob *= self.schedule['weekend_multiplier']

        # Peak hour boost
        if in_peak:
            base_prob *= 3.0

        # Binge mode — occasional high-activity bursts
        if random.random() < self.schedule['binge_probability']:
            base_prob *= 4.0

        return random.random() < base_prob

    def human_delay(self) -> float:
        """
        Returns seconds to wait before taking action.
        Simulates human 'thinking time' before posting.
        """
        # Human response time follows a log-normal distribution
        # Most responses: 30s-5min, occasional: up to 30min
        mu = math.log(120)   # median 2 minutes
        sigma = 0.8
        delay = random.lognormvariate(mu, sigma)
        return min(delay, 1800)  # cap at 30 minutes

    def get_next_wakeup(self) -> int:
        """
        Returns seconds until this ghost's next check-in.
        Ghosts don't check constantly — they sleep like humans.
        """
        # Check in every 15-45 minutes during waking hours
        hour = datetime.now(timezone.utc).hour
        peak_hours = self.schedule['peak_hours_utc']

        if hour in peak_hours:
            return random.randint(900, 1800)   # 15-30 min during peak
        else:
            return random.randint(2700, 7200)  # 45-120 min off-peak


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: GHOST AGENT
# The main orchestrator — combines identity, content, and scheduling.
# In production, this runs as a long-lived process per ghost.
# ─────────────────────────────────────────────────────────────────────────────

class GhostAgent:
    """
    Manages a single ghost's lifecycle — schedules activity,
    generates content, and (in production) posts to Reddit.
    """

    def __init__(self, profile: GhostProfile, config: dict, dry_run: bool = True):
        self.profile = profile
        self.config = config
        self.dry_run = dry_run
        self.content_gen = ContentGenerator(profile, dry_run)
        self.scheduler = BehaviorScheduler(profile)
        self.reddit = None
        self._action_log = []

        if not dry_run and PRAW_AVAILABLE:
            self._init_reddit()

    def _init_reddit(self):
        """Initialize Reddit connection. Requires credentials in config."""
        required = ['reddit_client_id', 'reddit_client_secret',
                    'reddit_username', 'reddit_password']
        if not all(k in self.config for k in required):
            log.warning(f"[{self.profile.username}] Reddit credentials not configured — dry run mode")
            self.dry_run = True
            return
        try:
            self.reddit = praw.Reddit(
                client_id=self.config['reddit_client_id'],
                client_secret=self.config['reddit_client_secret'],
                username=self.config['reddit_username'],
                password=self.config['reddit_password'],
                user_agent=f"CHAFF:ghost_engine:v0.1 (by u/{self.config['reddit_username']})"
            )
            log.info(f"[{self.profile.username}] Reddit connected")
        except Exception as e:
            log.error(f"[{self.profile.username}] Reddit connection failed: {e}")
            self.dry_run = True

    def run_cycle(self):
        """One activity cycle — decides what to do and does it."""
        p = self.profile

        if not self.scheduler.should_post_now():
            log.debug(f"[{p.username}] Quiet this hour — skipping")
            return

        # Choose action weighted by personality
        actions = ['comment', 'comment', 'browse']  # comments > posts for new accounts
        if p.personality.extraversion > 0.6:
            actions.append('post')
        if p.personality.conscientiousness > 0.7:
            actions.append('comment')

        action = random.choice(actions)
        if not p.interests:
            log.warning(f"[{p.username}] No interests configured — skipping")
            return
        subreddit = random.choice(p.interests)

        log.info(f"[{p.username}] Taking action: {action} in r/{subreddit}")

        # Human delay before acting
        delay = self.scheduler.human_delay()
        log.info(f"[{p.username}] Waiting {delay:.0f}s (human delay)")
        if not self.dry_run:
            time.sleep(delay)

        if action == 'comment':
            self._do_comment(subreddit)
        elif action == 'post':
            self._do_post(subreddit)
        elif action == 'browse':
            self._do_browse(subreddit)

    def _do_comment(self, subreddit_name: str):
        """Comment on a recent post in a subreddit."""
        try:
            if self.dry_run or not self.reddit:
                # Simulate with a hot post title
                fake_title = f"[DRY RUN] Interesting discussion in r/{subreddit_name}"
                content = self.content_gen.generate_comment(subreddit_name, fake_title)
                self._log_action('comment', subreddit_name, content)
                return

            sub = self.reddit.subreddit(subreddit_name)
            posts = list(sub.hot(limit=25))
            if not posts:
                return

            # Pick a post — prefer posts with some comments but not mega-threads
            candidates = [p for p in posts if 5 < p.num_comments < 200]
            if not candidates:
                candidates = posts
            post = random.choice(candidates[:10])

            content = self.content_gen.generate_comment(
                subreddit_name, post.title, post.selftext
            )
            post.reply(content)
            self._log_action('comment', subreddit_name, content, post.title)
            log.info(f"[{self.profile.username}] Commented on '{post.title[:50]}...'")

        except Exception as e:
            log.error(f"[{self.profile.username}] Comment failed: {e}")

    def _do_post(self, subreddit_name: str):
        """Submit a new post to a subreddit."""
        try:
            title, body = self.content_gen.generate_post(subreddit_name)
            if not title:
                return

            if self.dry_run or not self.reddit:
                self._log_action('post', subreddit_name, f"{title}\n\n{body}")
                return

            sub = self.reddit.subreddit(subreddit_name)
            sub.submit(title=title, selftext=body)
            self._log_action('post', subreddit_name, f"{title}\n\n{body}")
            log.info(f"[{self.profile.username}] Posted: '{title[:50]}...'")

        except Exception as e:
            log.error(f"[{self.profile.username}] Post failed: {e}")

    def _do_browse(self, subreddit_name: str):
        """Browse a subreddit (upvote/read without commenting)."""
        log.info(f"[{self.profile.username}] Browsing r/{subreddit_name} (no action)")
        self._log_action('browse', subreddit_name, "")
        # In production: read posts, maybe upvote, leave no trace beyond server logs

    def _log_action(self, action: str, subreddit: str, content: str, context: str = ""):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ghost": self.profile.username,
            "action": action,
            "subreddit": subreddit,
            "content_preview": content[:100],
            "context": context[:80],
        }
        self._action_log.append(entry)
        if action != 'browse':
            mode = "[DRY RUN]" if self.dry_run else "[LIVE]"
            log.info(f"{mode} [{self.profile.username}] {action.upper()} r/{subreddit}: {content[:60]}...")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5: NETWORK COORDINATOR
# Manages multiple ghost agents, coordinates seeds, tracks health.
# This is the local-node equivalent of the P2P network coordinator.
# ─────────────────────────────────────────────────────────────────────────────

class GhostNetwork:
    """
    Manages a local pool of ghost agents.
    In Phase 2, this will be replaced by the P2P network layer.
    """

    def __init__(self, seeds: list[str], config: dict, dry_run: bool = True):
        self.config = config
        self.dry_run = dry_run
        self.agents: list[GhostAgent] = []

        log.info(f"Initializing CHAFF Ghost Network -- {len(seeds)} ghost(s)")
        for seed in seeds:
            profile = GhostGenerator(seed).generate()
            agent = GhostAgent(profile, config, dry_run)
            self.agents.append(agent)
            log.info(f"  Ghost ready: {profile.username} ({profile.age}yo {profile.occupation} in {profile.location_city})")

    def run_all(self):
        """Run one activity cycle for all ghosts."""
        for agent in self.agents:
            try:
                agent.run_cycle()
                # Small gap between agents to avoid burst patterns
                time.sleep(random.uniform(5, 30))
            except Exception as e:
                log.error(f"Agent {agent.profile.username} crashed: {e}")

    def print_profiles(self):
        """Print ghost profiles for inspection."""
        for agent in self.agents:
            p = agent.profile
            print(f"\n{'='*60}")
            print(f"Ghost: {p.username}")
            print(f"  Age: {p.age} | Location: {p.location_city}, {p.location_state}")
            print(f"  Occupation: {p.occupation} | Education: {p.education}")
            print(f"  Personality: O={p.personality.openness:.2f} C={p.personality.conscientiousness:.2f} "
                  f"E={p.personality.extraversion:.2f} A={p.personality.agreeableness:.2f} "
                  f"N={p.personality.neuroticism:.2f}")
            print(f"  Interests: {', '.join(p.interests)}")
            print(f"  Posts/day avg: {p.posting_schedule['avg_posts_per_day']:.2f}")
            print(f"  Peak hours (UTC): {p.posting_schedule['peak_hours_utc']}")
            print(f"  Account age: {(datetime.now() - p.created_date).days} days")
            print(f"  Life context: {'; '.join(p.life_events)}")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6: DETECTION MONITOR
# Checks whether ghost accounts are being flagged or shadowbanned.
# Feeds intelligence back into the evasion system (Phase 4).
# ─────────────────────────────────────────────────────────────────────────────

class DetectionMonitor:
    """
    Monitors ghost account health and detection signals.
    Currently: basic shadowban check for Reddit.
    Phase 4: will feed evasion intelligence to P2P network.
    """

    @staticmethod
    def check_shadowban(username: str) -> dict:
        """
        Check if a Reddit account is shadowbanned.
        Shadowbanned accounts' posts are invisible to others.
        """
        import requests
        url = f"https://www.reddit.com/user/{username}/about.json"
        headers = {"User-Agent": "CHAFF DetectionMonitor v0.1"}
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 404:
                return {"status": "banned_or_deleted", "username": username}
            if r.status_code == 200:
                data = r.json()
                if data.get("data", {}).get("is_suspended"):
                    return {"status": "suspended", "username": username}
                return {"status": "active", "username": username,
                        "karma": data["data"].get("total_karma", 0)}
            return {"status": "unknown", "code": r.status_code, "username": username}
        except Exception as e:
            return {"status": "error", "error": str(e), "username": username}


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRYPOINT
# ─────────────────────────────────────────────────────────────────────────────

def main():
    if sys.stdout.encoding and 'utf' not in sys.stdout.encoding.lower():
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(
        description='CHAFF Ghost Engine — Synthetic privacy noise generation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ghost_engine.py --dry-run                          # Generate 1 ghost, show profile
  python ghost_engine.py --seed abc123 --dry-run            # Specific seed, dry run
  python ghost_engine.py --count 3 --dry-run                # 3 ghosts, show all profiles
  python ghost_engine.py --seed abc123 --run-once           # One live cycle (needs Reddit creds)
  python ghost_engine.py --seed abc123 --run-continuous     # Continuous operation (production)
  python ghost_engine.py --check-health myusername          # Check if account is shadowbanned
        """
    )
    parser.add_argument('--seed', type=str, default='chaff_default_seed_001',
                        help='Seed for ghost generation (default: chaff_default_seed_001)')
    parser.add_argument('--count', type=int, default=1,
                        help='Number of ghosts to generate (default: 1)')
    parser.add_argument('--dry-run', action='store_true', default=True,
                        help='Dry run — generate profiles and simulate actions without posting (default: True)')
    parser.add_argument('--live', action='store_true',
                        help='Live mode — actually post to Reddit (requires credentials in config.json)')
    parser.add_argument('--run-once', action='store_true',
                        help='Run one activity cycle and exit')
    parser.add_argument('--run-continuous', action='store_true',
                        help='Run continuously on schedule (production mode)')
    parser.add_argument('--profiles-only', action='store_true',
                        help='Just print ghost profiles and exit')
    parser.add_argument('--check-health', type=str, metavar='USERNAME',
                        help='Check if a Reddit username is shadowbanned')
    parser.add_argument('--config', type=str, default='config.json',
                        help='Path to config file (default: config.json)')
    parser.add_argument('--verbose', action='store_true',
                        help='Verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Health check mode
    if args.check_health:
        result = DetectionMonitor.check_shadowban(args.check_health)
        print(f"\nHealth check for u/{args.check_health}:")
        print(json.dumps(result, indent=2))
        return

    # Load config
    config = {}
    try:
        with open(args.config) as f:
            config = json.load(f)
    except FileNotFoundError:
        if not args.dry_run and args.live:
            log.warning(f"Config file '{args.config}' not found. Running in dry-run mode.")

    dry_run = not args.live

    # Generate seeds
    seeds = []
    for i in range(args.count):
        seed = f"{args.seed}_{i:04d}" if args.count > 1 else args.seed
        seeds.append(seed)

    print(f"""
+----------------------------------------------------------+
|       PROJECT CHAFF -- Ghost Engine v0.1.0               |
|     Because the best defense against radar is noise.     |
+----------------------------------------------------------+

Mode: {'DRY RUN (no actual posting)' if dry_run else 'LIVE MODE -- WILL ACTUALLY POST'}
Ghosts: {args.count}
Seeds: {seeds}
LLM: {'Ollama available' if OLLAMA_AVAILABLE else 'Template fallback (install Ollama for better content)'}
""")

    # Initialize network
    network = GhostNetwork(seeds, config, dry_run=dry_run)

    # Profiles only mode
    if args.profiles_only:
        network.print_profiles()
        return

    # Default dry-run behavior: show profiles and run one simulated cycle
    if dry_run and not args.run_once and not args.run_continuous:
        network.print_profiles()
        print("\n[DRY RUN] Running one simulated cycle...\n")
        network.run_all()
        return

    # Single cycle
    if args.run_once:
        log.info("Running single activity cycle...")
        network.run_all()
        log.info("Cycle complete.")
        return

    # Continuous mode
    if args.run_continuous:
        if not SCHEDULE_AVAILABLE:
            log.error("Continuous mode requires the 'schedule' module. Install: pip install schedule")
            return
        log.info("Starting continuous operation. Press Ctrl+C to stop.")
        log.info(f"Ghost check-in interval: every 15-120 minutes (randomized)")

        def cycle():
            log.info("=== Ghost cycle starting ===")
            network.run_all()
            # Schedule next run with randomized delay
            next_delay = random.randint(15, 90)  # minutes
            log.info(f"Next cycle in {next_delay} minutes")
            schedule.clear('ghost_cycle')
            schedule.every(next_delay).minutes.do(cycle).tag('ghost_cycle')

        cycle()  # run immediately
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            log.info("Ghost engine stopped. Ghosts going to sleep.")


if __name__ == '__main__':
    main()
