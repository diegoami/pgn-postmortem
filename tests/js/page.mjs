// A stand-in page and storage for the reading-history script's tests
// (pgn_postmortem/static/history.js). No npm packages: the pages are parsed by
// a small tokenizer that is enough for the well-formed HTML the site builder
// writes, and the script runs in a fresh V8 context (node:vm) with only
// `window` and `document` as globals, as a browser gives it.

import { readFileSync } from "node:fs";
import vm from "node:vm";

export const REPO = new URL("../../", import.meta.url);
export const SCRIPT_PATH = new URL("pgn_postmortem/static/history.js", REPO);
export const GOLDEN = new URL("tests/golden/site/", REPO);

const VOID = new Set(["meta", "link", "br", "img", "input", "hr"]);
const RAW = new Set(["script", "style"]);
const ENTITIES = { amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", "#x27": "'", "#39": "'" };

function decode(text) {
  return text.replace(/&(amp|lt|gt|quot|apos|#x27|#39);/g, (_, name) => ENTITIES[name]);
}

class Text {
  constructor(text) {
    this.data = text;
    this.parentNode = null;
  }
  get textContent() {
    return this.data;
  }
}

export class Element {
  constructor(tag, doc) {
    this.tagName = tag.toUpperCase();
    this.ownerDocument = doc;
    this.attributes = new Map();
    this.childNodes = [];
    this.parentNode = null;
    this.listeners = new Map();
  }
  getAttribute(name) {
    return this.attributes.has(name) ? this.attributes.get(name) : null;
  }
  setAttribute(name, value) {
    this.attributes.set(name, String(value));
  }
  removeAttribute(name) {
    this.attributes.delete(name);
  }
  hasAttribute(name) {
    return this.attributes.has(name);
  }
  get hidden() {
    return this.hasAttribute("hidden");
  }
  set hidden(value) {
    if (value) this.setAttribute("hidden", "");
    else this.removeAttribute("hidden");
  }
  get open() {
    return this.hasAttribute("open");
  }
  set open(value) {
    if (value) this.setAttribute("open", "");
    else this.removeAttribute("open");
  }
  get className() {
    return this.getAttribute("class") || "";
  }
  set className(value) {
    this.setAttribute("class", value);
  }
  get id() {
    return this.getAttribute("id") || "";
  }
  get textContent() {
    return this.childNodes.map((node) => node.textContent).join("");
  }
  set textContent(value) {
    for (const node of this.childNodes) node.parentNode = null;
    this.childNodes = [];
    if (value !== "") this.appendChild(new Text(String(value)));
  }
  get children() {
    return this.childNodes.filter((node) => node instanceof Element);
  }
  appendChild(node) {
    if (node.parentNode) node.parentNode.removeChild(node);
    node.parentNode = this;
    this.childNodes.push(node);
    return node;
  }
  insertBefore(node, reference) {
    if (reference === null) return this.appendChild(node);
    if (node.parentNode) node.parentNode.removeChild(node);
    const i = this.childNodes.indexOf(reference);
    if (i < 0) throw new Error("the reference is not a child");
    node.parentNode = this;
    this.childNodes.splice(i, 0, node);
    return node;
  }
  removeChild(node) {
    const i = this.childNodes.indexOf(node);
    if (i < 0) throw new Error("not a child");
    this.childNodes.splice(i, 1);
    node.parentNode = null;
    return node;
  }
  addEventListener(type, listener) {
    if (!this.listeners.has(type)) this.listeners.set(type, []);
    this.listeners.get(type).push(listener);
  }
  // For the tests: fire an event at this element (no bubbling, as "toggle" and a button's "click" need).
  dispatch(type) {
    for (const listener of this.listeners.get(type) || []) listener.call(this, { type, target: this });
  }
  *descendants() {
    for (const child of this.children) {
      yield child;
      yield* child.descendants();
    }
  }
  getElementsByTagName(tag) {
    const upper = tag.toUpperCase();
    return [...this.descendants()].filter((e) => e.tagName === upper);
  }
}

export class Document {
  constructor() {
    this.root = new Element("#document", this);
  }
  get documentElement() {
    return this.root.children[0];
  }
  get head() {
    return this.getElementsByTagName("head")[0] || null;
  }
  get body() {
    return this.getElementsByTagName("body")[0] || null;
  }
  getElementsByTagName(tag) {
    return this.root.getElementsByTagName(tag);
  }
  getElementById(id) {
    return [...this.root.descendants()].find((e) => e.getAttribute("id") === id) || null;
  }
  createElement(tag) {
    return new Element(tag.toLowerCase(), this);
  }
  createTextNode(text) {
    return new Text(text);
  }
  // For the tests.
  byClass(tag, cls) {
    return this.getElementsByTagName(tag).filter((e) => e.className.split(/\s+/).includes(cls));
  }
}

const TOKEN = /<!--[\s\S]*?-->|<!DOCTYPE[^>]*>|<\/([a-zA-Z0-9]+)\s*>|<([a-zA-Z0-9]+)((?:\s+[^\s"'>/=]+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s"'>]+))?)*)\s*\/?>/g;
const ATTRIBUTE = /([^\s"'>/=]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>]+)))?/g;

export function parseHtml(html) {
  const doc = new Document();
  let current = doc.root;
  let at = 0;
  TOKEN.lastIndex = 0;
  for (let match = TOKEN.exec(html); match; match = TOKEN.exec(html)) {
    if (match.index > at) current.appendChild(new Text(decode(html.slice(at, match.index))));
    at = TOKEN.lastIndex;
    const [, closing, opening, attrs] = match;
    if (closing) {
      if (current.tagName !== closing.toUpperCase()) {
        throw new Error(`</${closing}> closes <${current.tagName.toLowerCase()}>`);
      }
      current = current.parentNode;
    } else if (opening) {
      const element = doc.createElement(opening);
      for (const a of (attrs || "").matchAll(ATTRIBUTE)) {
        element.setAttribute(a[1], decode(a[2] ?? a[3] ?? a[4] ?? ""));
      }
      current.appendChild(element);
      if (RAW.has(element.tagName.toLowerCase())) {
        const end = html.indexOf(`</${opening}>`, at);
        element.appendChild(new Text(html.slice(at, end)));
        at = end + opening.length + 3;
        TOKEN.lastIndex = at;
      } else if (!VOID.has(element.tagName.toLowerCase())) {
        current = element;
      }
    }
  }
  if (current !== doc.root) throw new Error(`<${current.tagName.toLowerCase()}> is never closed`);
  return doc;
}

// localStorage as a browser gives it: strings in, strings out, keys by index.
export class MemoryStorage {
  constructor(entries = {}) {
    this.map = new Map(Object.entries(entries).map(([k, v]) => [k, String(v)]));
    this.writes = 0;
  }
  get length() {
    return this.map.size;
  }
  key(i) {
    return [...this.map.keys()][i] ?? null;
  }
  getItem(key) {
    return this.map.has(key) ? this.map.get(key) : null;
  }
  setItem(key, value) {
    this.writes += 1;
    this.map.set(String(key), String(value));
  }
  removeItem(key) {
    this.map.delete(key);
  }
  clear() {
    this.map.clear();
  }
  entries() {
    return Object.fromEntries(this.map);
  }
}

export function golden(name) {
  return readFileSync(new URL(name, GOLDEN), "utf8");
}

// The script exactly as the pages inline it.
export function scriptSource() {
  return readFileSync(SCRIPT_PATH, "utf8");
}

// Run the script on a page. `window` is a plain object: its localStorage is
// `storage` (or a getter that throws, with `storage: "throws"`; or missing,
// with `storage: undefined`), and confirm() answers `confirm`.
export function run(html, { storage, confirm = () => true } = {}) {
  const document = parseHtml(html);
  const confirms = [];
  const window = {
    document,
    confirm(message) {
      confirms.push(message);
      return typeof confirm === "function" ? confirm(message) : confirm;
    },
  };
  if (storage === "throws") {
    Object.defineProperty(window, "localStorage", {
      get() {
        throw new Error("SecurityError: access to localStorage is denied");
      },
    });
  } else if (storage !== undefined) {
    window.localStorage = storage;
  }
  vm.runInNewContext(scriptSource(), { window, document });
  return { document, window, confirms };
}
