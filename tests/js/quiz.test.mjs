// The quiz page's "answered" marks (ROADMAP.md F-9), added by the reading-history
// script (pgn_postmortem/static/history.js), run on the golden pages of
// tests/golden/site/ with a stand-in page and storage (./page.mjs).
// The gate: node --test 'tests/js/*.test.mjs'

import assert from "node:assert/strict";
import { test } from "node:test";

import { MemoryStorage, golden, run } from "./page.mjs";

const QUIZ = golden("quiz.html");
const INDEX = golden("index.html");
const MATE = "games/2020-06-01-9705c13f05.html"; // Ada Example's one own question: 3... Nf6 (3b)
const SITE = /<html lang="en" data-site="([^"]+)">/.exec(QUIZ)[1];
const P = `pgn-postmortem:${SITE}:`;
const LINE = /<li data-game="([^"]+)" data-move="([^"]+)">.*<\/li>\n/;

function revealedKey(id, move) {
  return `${P}revealed:${id}:${move}`;
}

// The golden quiz with these questions, [id, move] each, in this order: copies of its one line.
function quizWith(questions) {
  const [line, id, move] = LINE.exec(QUIZ);
  const lines = questions
    .map(([i, m], rank) =>
      line
        .replaceAll(`data-game="${id}"`, `data-game="${i}"`)
        .replace(`data-move="${move}"`, `data-move="${m}"`)
        .replace(/<span class="rank">\d+\.<\/span>/, `<span class="rank">${rank + 1}.</span>`),
    )
    .join("");
  return QUIZ.replace(line, lines);
}

// The questions as the page shows them now, in its order: [id, move, its mark or null].
function questions(document) {
  const list = document.getElementById("quiz");
  return list.getElementsByTagName("li").map((li) => {
    const mark = li.children.find((e) => e.className === "seen");
    return [li.getAttribute("data-game"), li.getAttribute("data-move"), mark ? mark.textContent : null];
  });
}

const SIX = [
  ["9705c13f05", "3b"],
  ["a9c90416b2", "5b"],
  ["9705c13f05", "12w"],
  ["9137b96576", "5w"],
  ["5ce208cdcb", "2b"],
  ["bf58e2afa0", "7w"],
];

test("the golden quiz carries what the script reads", () => {
  assert.equal(LINE.exec(QUIZ)[1], "9705c13f05");
  assert.equal(LINE.exec(QUIZ)[2], "3b");
  assert.deepEqual(questions(run(QUIZ, { storage: new MemoryStorage() }).document), [["9705c13f05", "3b", null]]);
  assert.equal(QUIZ.includes('id="history"'), false); // no history section: the index's code stays out
});

test("a question is marked answered when its game and move are in this site's history", () => {
  const storage = new MemoryStorage({
    [revealedKey("9705c13f05", "3b")]: "1",
    [revealedKey("9137b96576", "5w")]: "1",
    [revealedKey("a9c90416b2", "7w")]: "1", // that game's other move: not a question here
    [revealedKey("5ce208cdcb", "2b")]: "true", // not a revealed answer's value
    [`pgn-postmortem:another-book:revealed:bf58e2afa0:7w`]: "1", // another site's
    [`${P}viewed:a9c90416b2`]: "2000", // viewed is not answered
  });
  const { document } = run(quizWith(SIX), { storage });
  assert.deepEqual(questions(document), [
    ["9705c13f05", "3b", "answered"],
    ["a9c90416b2", "5b", null],
    ["9705c13f05", "12w", null], // the same game, another move
    ["9137b96576", "5w", "answered"],
    ["5ce208cdcb", "2b", null],
    ["bf58e2afa0", "7w", null],
  ]);
  // the mark is on the question's first line, after the points and before its date and opponent
  const first = document.getElementById("quiz").getElementsByTagName("li")[0];
  assert.deepEqual(
    first.children.map((e) => `${e.tagName.toLowerCase()}.${e.className}`),
    ["span.rank", "a.", "span.lost", "span.seen", "span.meta"],
  );
  const [style] = document.getElementsByTagName("style"); // its styling comes with it, into the head
  assert.equal(style.parentNode, document.head);
  assert.match(style.textContent, /\.seen \{/);
});

test("revealing an answer in its article marks it on the quiz", () => {
  const storage = new MemoryStorage();
  const { document: article } = run(golden(MATE), { storage });
  const [answer] = article.byClass("details", "answer");
  answer.open = true;
  answer.dispatch("toggle");
  assert.deepEqual(questions(run(QUIZ, { storage }).document), [["9705c13f05", "3b", "answered"]]);
});

test("the order never changes, and the quiz stores nothing", () => {
  const storage = new MemoryStorage({ [revealedKey("5ce208cdcb", "2b")]: "1", [revealedKey("9705c13f05", "3b")]: "1" });
  const before = { ...storage.entries() };
  const { document, window } = run(quizWith(SIX), { storage });
  const order = () => questions(document).map(([id, move]) => `${id}:${move}`);
  const ranks = () => document.getElementById("quiz").getElementsByTagName("li").map((li) => li.children[0].textContent);
  const expected = SIX.map(([id, move]) => `${id}:${move}`);
  assert.deepEqual(order(), expected);
  assert.deepEqual(ranks(), ["1.", "2.", "3.", "4.", "5.", "6."]);
  storage.setItem(revealedKey("bf58e2afa0", "7w"), "1"); // the last one answered meanwhile
  window.dispatch("pageshow", { persisted: true });
  assert.deepEqual(order(), expected);
  assert.deepEqual(ranks(), ["1.", "2.", "3.", "4.", "5.", "6."]);
  assert.deepEqual(
    questions(document).map(([, , mark]) => mark),
    ["answered", null, null, null, "answered", "answered"],
  );
  storage.removeItem(revealedKey("bf58e2afa0", "7w"));
  assert.deepEqual(storage.entries(), before); // nothing viewed, revealed or otherwise written by the quiz
});

test("Clear history on the index removes the marks", () => {
  const storage = new MemoryStorage({
    [revealedKey("9705c13f05", "3b")]: "1",
    [`${P}viewed:9705c13f05`]: "2000",
  });
  const quiz = run(QUIZ, { storage });
  assert.deepEqual(questions(quiz.document), [["9705c13f05", "3b", "answered"]]);

  const index = run(INDEX, { storage, confirm: () => true });
  index.document.getElementById("history-clear").dispatch("click");
  assert.deepEqual(storage.entries(), {});
  // opened again, and shown again from the back/forward cache: no mark
  assert.deepEqual(questions(run(QUIZ, { storage }).document), [["9705c13f05", "3b", null]]);
  quiz.window.dispatch("pageshow", { persisted: true });
  assert.deepEqual(questions(quiz.document), [["9705c13f05", "3b", null]]);
  // and the quiz has no button of its own
  assert.equal(quiz.document.getElementById("history-clear"), null);
  assert.equal(quiz.document.getElementsByTagName("button").length, 0);
});

for (const [name, storage] of [
  ["missing", undefined],
  ["null", null],
  ["a getter that throws", "throws"],
  [
    "writes that throw",
    Object.assign(new MemoryStorage({ [revealedKey("9705c13f05", "3b")]: "1" }), {
      setItem() {
        throw new Error("QuotaExceededError");
      },
    }),
  ],
  [
    "reads that throw",
    Object.assign(new MemoryStorage({ [revealedKey("9705c13f05", "3b")]: "1" }), {
      getItem() {
        throw new Error("SecurityError");
      },
    }),
  ],
]) {
  test(`with storage that is ${name} there are no marks and the quiz still works`, () => {
    const { document, window } = run(quizWith(SIX), { storage });
    assert.deepEqual(
      questions(document),
      SIX.map(([id, move]) => [id, move, null]),
    );
    assert.equal(document.getElementsByTagName("style").length, 0);
    assert.doesNotThrow(() => window.dispatch("pageshow", { persisted: true }));
    // every line still links to its question
    const links = document.getElementById("quiz").getElementsByTagName("a").map((a) => a.getAttribute("href"));
    assert.equal(links.length, 6);
    assert.ok(links.every((href) => /^games\/[^#]+\.html#moment-[1-9][0-9]{0,3}$/.test(href)), links);
  });
}

test("a quiz shown again from the back/forward cache redraws the marks", () => {
  const storage = new MemoryStorage();
  const { document, window } = run(quizWith(SIX), { storage });
  assert.deepEqual(questions(document).filter(([, , mark]) => mark), []);

  // meanwhile, in the articles: two answers revealed
  storage.setItem(revealedKey("a9c90416b2", "5b"), "1");
  storage.setItem(revealedKey("5ce208cdcb", "2b"), "1");
  window.dispatch("pageshow", { persisted: false }); // the first showing, right after loading: nothing new
  assert.deepEqual(questions(document).filter(([, , mark]) => mark), []);
  window.dispatch("pageshow", { persisted: true });
  assert.deepEqual(
    questions(document).filter(([, , mark]) => mark),
    [
      ["a9c90416b2", "5b", "answered"],
      ["5ce208cdcb", "2b", "answered"],
    ],
  );
  // shown again twice: one mark each, not two
  window.dispatch("pageshow", { persisted: true });
  const marks = document.getElementById("quiz").getElementsByTagName("span").filter((e) => e.className === "seen");
  assert.equal(marks.length, 2);

  // and one of them forgotten elsewhere: its mark goes
  storage.removeItem(revealedKey("a9c90416b2", "5b"));
  window.dispatch("pageshow", { persisted: true });
  assert.deepEqual(
    questions(document).filter(([, , mark]) => mark),
    [["5ce208cdcb", "2b", "answered"]],
  );
});

test("lines with a malformed game or move are left unmarked", () => {
  const html = quizWith([
    ["9705c13f05", "3b"],
    ["bad id!", "3b"],
    ["9705c13f05", "0w"],
  ]);
  const storage = new MemoryStorage({
    [revealedKey("9705c13f05", "3b")]: "1",
    [revealedKey("bad id!", "3b")]: "1",
    [revealedKey("9705c13f05", "0w")]: "1",
  });
  assert.deepEqual(questions(run(html, { storage }).document), [
    ["9705c13f05", "3b", "answered"],
    ["bad id!", "3b", null],
    ["9705c13f05", "0w", null],
  ]);
});
