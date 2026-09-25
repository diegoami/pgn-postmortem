// The reading-history script (pgn_postmortem/static/history.js, ROADMAP.md F-8),
// run on the golden pages of tests/golden/site/ with a stand-in page and
// storage (./page.mjs). The gate: node --test 'tests/js/*.test.mjs'

import assert from "node:assert/strict";
import { test } from "node:test";

import { MemoryStorage, golden, run } from "./page.mjs";

const INDEX = golden("index.html");
const MATE = "games/2020-06-01-9705c13f05.html"; // one question: 3... Nf6 (3b)
const QUIET = "games/2019-03-14-bf58e2afa0.html"; // analyzed, no question
const SITE = /<html lang="en" data-site="([^"]+)">/.exec(INDEX)[1];
const P = `pgn-postmortem:${SITE}:`;

function viewedKey(id) {
  return `${P}viewed:${id}`;
}

function revealedKey(id, move) {
  return `${P}revealed:${id}:${move}`;
}

// The index's games, in its order: [id, moves of its current questions].
function indexGames(html = INDEX) {
  return [...html.matchAll(/<li data-game="([^"]+)" data-moves="([^"]*)">/g)].map((m) => [m[1], m[2]]);
}

// The golden index with `extra` more games, each a copy of the first game's entry under a new id.
function indexWith(extra) {
  const first = /<li data-game="([^"]+)" data-moves="[^"]*">.*<\/li>\n/.exec(INDEX);
  const copies = extra.map((id) => first[0].replaceAll(first[1], id)).join("");
  return INDEX.replace(first[0], first[0] + copies);
}

function recent(document) {
  const list = document.getElementById("history-recent");
  return list.getElementsByTagName("li").map((li) => {
    const link = li.getElementsByTagName("a")[0];
    return link.getAttribute("href");
  });
}

function marks(document) {
  const found = {};
  for (const li of document.getElementsByTagName("li")) {
    const id = li.getAttribute("data-game");
    if (!id) continue;
    const mark = li.children.find((e) => e.className === "seen");
    if (mark) found[id] = mark.textContent;
  }
  return found;
}

function section(document) {
  return document.getElementById("history");
}

test("the pages carry what the script reads", () => {
  assert.match(SITE, /^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/);
  assert.equal(indexGames().length, 6);
  assert.ok(section(run(INDEX, { storage: new MemoryStorage() }).document), "no history section on the index");
});

test("opening an article records the game as viewed", () => {
  const storage = new MemoryStorage();
  const before = Date.now();
  run(golden(MATE), { storage });
  const after = Date.now();
  const stored = storage.getItem(viewedKey("9705c13f05"));
  assert.match(stored ?? "", /^[0-9]+$/);
  assert.ok(Number(stored) >= before && Number(stored) <= after, stored);
  assert.deepEqual(Object.keys(storage.entries()), [viewedKey("9705c13f05")]); // nothing else, no answer yet
});

test("opening it again moves it to the latest time", () => {
  const storage = new MemoryStorage({ [viewedKey("9705c13f05")]: "1000" });
  run(golden(MATE), { storage });
  assert.ok(Number(storage.getItem(viewedKey("9705c13f05"))) > 1000);
});

test("revealing an answer records it once, keyed by move", () => {
  const storage = new MemoryStorage();
  const { document } = run(golden(MATE), { storage });
  const [answer] = document.byClass("details", "answer");
  assert.equal(answer.getAttribute("data-move"), "3b");
  assert.equal(storage.getItem(revealedKey("9705c13f05", "3b")), null, "recorded before it was opened");

  answer.open = true;
  answer.dispatch("toggle");
  answer.open = false;
  answer.dispatch("toggle"); // closing it again keeps the record
  answer.open = true;
  answer.dispatch("toggle");
  const revealed = Object.entries(storage.entries()).filter(([key]) => key.startsWith(`${P}revealed:`));
  assert.deepEqual(revealed, [[revealedKey("9705c13f05", "3b"), "1"]]);
});

test("an answer already open when the page loads is recorded", () => {
  const storage = new MemoryStorage();
  run(golden(MATE).replace('<details class="answer" data-move="3b">', '<details class="answer" data-move="3b" open>'), {
    storage,
  });
  assert.equal(storage.getItem(revealedKey("9705c13f05", "3b")), "1");
});

test("the index lists the latest 10 games newest first, and only games in its current list", () => {
  const extra = Array.from({ length: 8 }, (_, i) => `extra0000${i}`);
  const html = indexWith(extra);
  const ids = indexGames(html).map(([id]) => id);
  assert.equal(ids.length, 14);
  const storage = new MemoryStorage({
    // viewed long ago, and more recently than every game of the index: but not in its list
    [viewedKey("gone000000")]: "999999999999",
    [`pgn-postmortem:another-book:viewed:${ids[0]}`]: "999999999998",
  });
  ids.slice(0, 12).forEach((id, i) => storage.setItem(viewedKey(id), String(1000 + i)));

  const { document } = run(html, { storage });
  const hrefs = recent(document);
  const expected = ids
    .slice(2, 12)
    .reverse()
    .map((id) => {
      const href = new RegExp(`<li data-game="${id}" data-moves="[^"]*"><a href="([^"]+)">`).exec(html)[1];
      return href;
    });
  assert.equal(hrefs.length, 10);
  assert.deepEqual(hrefs, expected);
  assert.equal(section(document).hidden, false);
  assert.deepEqual(Object.keys(marks(document)).sort(), ids.slice(0, 12).sort()); // every viewed game is marked
});

test("with nothing viewed, the history stays hidden and nothing is marked", () => {
  const storage = new MemoryStorage({ [`pgn-postmortem:another-book:viewed:9705c13f05`]: "5000" });
  const { document } = run(INDEX, { storage });
  assert.equal(section(document).hidden, true);
  assert.deepEqual(marks(document), {});
  assert.deepEqual(recent(document), []);
});

test("the k/m mark counts only answers of the game's current questions", () => {
  const storage = new MemoryStorage({
    [viewedKey("9705c13f05")]: "2000",
    [viewedKey("bf58e2afa0")]: "1000",
    [viewedKey("a9c90416b2")]: "3000",
    [revealedKey("9705c13f05", "3b")]: "1",
    [revealedKey("9705c13f05", "12w")]: "1", // a question no longer asked
    [revealedKey("a9c90416b2", "7w")]: "1", // not this game's question (5b is)
  });
  const games = Object.fromEntries(indexGames());
  assert.equal(games["9705c13f05"], "3b");
  assert.equal(games["a9c90416b2"], "5b");
  assert.equal(games["bf58e2afa0"], "");

  const { document } = run(INDEX, { storage });
  assert.deepEqual(marks(document), {
    "9705c13f05": "viewed · 1/1 answer",
    a9c90416b2: "viewed · 0/1 answer",
    bf58e2afa0: "viewed",
  });
  // the recent list carries the same marks
  const list = document.getElementById("history-recent").getElementsByTagName("li");
  assert.deepEqual(
    list.map((li) => li.children.find((e) => e.className === "seen").textContent),
    ["viewed · 0/1 answer", "viewed · 1/1 answer", "viewed"],
  );
});

test("the k/m mark counts several questions", () => {
  const html = INDEX.replace('data-game="9705c13f05" data-moves="3b"', 'data-game="9705c13f05" data-moves="3b 9w 14b 20w"');
  const storage = new MemoryStorage({
    [viewedKey("9705c13f05")]: "2000",
    [revealedKey("9705c13f05", "3b")]: "1",
    [revealedKey("9705c13f05", "14b")]: "1",
  });
  assert.deepEqual(marks(run(html, { storage }).document), { "9705c13f05": "viewed · 2/4 answers" });
});

test("Clear history removes this site's keys only, and only after the confirmation", () => {
  const others = {
    [`pgn-postmortem:another-book:viewed:9705c13f05`]: "5000",
    [`pgn-postmortem:another-book:revealed:9705c13f05:3b`]: "1",
    [`pgn-postmortem:${SITE}x:viewed:9705c13f05`]: "5000", // a site key that starts with this one
    theme: "dark",
  };
  const ours = {
    [viewedKey("9705c13f05")]: "2000",
    [viewedKey("gone000000")]: "2500", // a game no longer in the list: still this site's
    [revealedKey("9705c13f05", "3b")]: "1",
    [`${P}viewed:corrupt`]: "{not json",
  };
  const storage = new MemoryStorage({ ...others, ...ours });
  let answer = false;
  const { document, confirms } = run(INDEX, { storage, confirm: () => answer });
  const button = document.getElementById("history-clear");
  assert.equal(button.tagName, "BUTTON");

  button.dispatch("click"); // the reader says no
  assert.equal(confirms.length, 1);
  assert.deepEqual(storage.entries(), { ...others, ...ours });
  assert.equal(section(document).hidden, false);

  answer = true;
  button.dispatch("click");
  assert.equal(confirms.length, 2);
  assert.deepEqual(storage.entries(), others);
  assert.equal(section(document).hidden, true);
  assert.deepEqual(marks(document), {});
  assert.deepEqual(recent(document), []);
});

for (const [name, storage] of [
  ["missing", undefined],
  ["null", null],
  ["a getter that throws", "throws"],
  [
    "writes that throw",
    Object.assign(new MemoryStorage({ [viewedKey("9705c13f05")]: "2000" }), {
      setItem() {
        throw new Error("QuotaExceededError");
      },
    }),
  ],
  [
    "reads that throw",
    Object.assign(new MemoryStorage(), {
      getItem() {
        throw new Error("SecurityError");
      },
    }),
  ],
]) {
  test(`storage that is ${name} leaves the page working with the history hidden`, () => {
    const index = run(INDEX, { storage });
    assert.equal(section(index.document).hidden, true);
    assert.deepEqual(marks(index.document), {});
    assert.deepEqual(recent(index.document), []);
    assert.equal(index.document.getElementsByTagName("style").length, 0);

    const article = run(golden(MATE), { storage });
    const [answer] = article.document.byClass("details", "answer");
    answer.open = true;
    assert.doesNotThrow(() => answer.dispatch("toggle"));
  });
}

test("corrupt stored data is ignored, not trusted", () => {
  const bad = ["", "abc", "-5", "1e12", "12.5", " 7", "{}", "[1]", "Infinity", "0", "99999999999999999999"];
  for (const value of bad) {
    const { document } = run(INDEX, { storage: new MemoryStorage({ [viewedKey("9705c13f05")]: value }) });
    assert.deepEqual(marks(document), {}, value);
    assert.equal(section(document).hidden, true, value);
  }

  for (const value of ["true", "0", "2", "yes", ""]) {
    const store = new MemoryStorage({ [viewedKey("9705c13f05")]: "2000", [revealedKey("9705c13f05", "3b")]: value });
    assert.deepEqual(marks(run(INDEX, { storage: store }).document), { "9705c13f05": "viewed · 0/1 answer" }, value);
  }
});

test("a page without a valid site key records nothing", () => {
  for (const html of [
    golden(MATE).replace(/ data-site="[^"]+"/, ""),
    golden(MATE).replace(/ data-site="[^"]+"/, ' data-site="a:b"'),
  ]) {
    const storage = new MemoryStorage();
    run(html, { storage });
    assert.deepEqual(storage.entries(), {});
  }
});

test("on the golden pages: open two games, reveal an answer, and the index shows both", () => {
  const storage = new MemoryStorage();
  run(golden(QUIET), { storage });
  const { document: article } = run(golden(MATE), { storage });
  const [answer] = article.byClass("details", "answer");
  answer.open = true;
  answer.dispatch("toggle");
  // the two opened within the same millisecond would tie; make the order certain
  storage.setItem(viewedKey("bf58e2afa0"), String(Number(storage.getItem(viewedKey("9705c13f05"))) - 1));

  const { document } = run(INDEX, { storage });
  assert.equal(section(document).hidden, false);
  assert.deepEqual(recent(document), [MATE, QUIET]);
  assert.deepEqual(marks(document), { "9705c13f05": "viewed · 1/1 answer", bf58e2afa0: "viewed" });
  // the mark is on the game's first line, after its result and before its date and event
  const entry = document.getElementsByTagName("li").find((li) => li.getAttribute("data-game") === "9705c13f05");
  assert.deepEqual(
    entry.children.map((e) => `${e.tagName.toLowerCase()}.${e.className}`),
    ["a.", "span.result", "span.seen", "span.meta"],
  );
  const [style] = document.getElementsByTagName("style"); // its styling comes with it, into the head
  assert.equal(style.parentNode, document.head);
  assert.match(style.textContent, /\.seen \{/);
});

// "Back" to a served page (http://, e.g. GitHub Pages) shows it again from the browser's back/forward cache:
// the script does not run again, only a "pageshow" event with persisted set comes.
test("an index shown again from the back/forward cache shows the history as stored now", () => {
  const storage = new MemoryStorage();
  const { document, window } = run(INDEX, { storage });
  assert.equal(section(document).hidden, true);

  // meanwhile, in the article: the game was opened and its answer revealed
  storage.setItem(viewedKey("9705c13f05"), "2000");
  storage.setItem(revealedKey("9705c13f05", "3b"), "1");
  window.dispatch("pageshow", { persisted: true });
  assert.equal(section(document).hidden, false);
  assert.deepEqual(recent(document), [MATE]);
  assert.deepEqual(marks(document), { "9705c13f05": "viewed · 1/1 answer" });

  // and cleared elsewhere (another tab): shown again, the stale marks go
  storage.clear();
  window.dispatch("pageshow", { persisted: true });
  assert.equal(section(document).hidden, true);
  assert.deepEqual(marks(document), {});
  assert.deepEqual(recent(document), []);
});

test("an article shown again from the back/forward cache is recorded as viewed again", () => {
  const storage = new MemoryStorage();
  const { window } = run(golden(MATE), { storage });
  storage.setItem(viewedKey("9705c13f05"), "1000");
  window.dispatch("pageshow", { persisted: false }); // the first showing, right after loading: nothing new
  assert.equal(storage.getItem(viewedKey("9705c13f05")), "1000");
  window.dispatch("pageshow", { persisted: true });
  assert.ok(Number(storage.getItem(viewedKey("9705c13f05"))) > 1000);
});
