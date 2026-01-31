window.pdocSearch = (function () {
  /** elasticlunr - http://weixsong.github.io * Copyright (C) 2017 Oliver Nightingale * Copyright (C) 2017 Wei Song * MIT Licensed */ !(function () {
    function e(e) {
      if (null === e || "object" != typeof e) return e;
      var t = e.constructor();
      for (var n in e) e.hasOwnProperty(n) && (t[n] = e[n]);
      return t;
    }
    var t = function (e) {
      var n = new t.Index();
      return (
        n.pipeline.add(t.trimmer, t.stopWordFilter, t.stemmer),
        e && e.call(n, n),
        n
      );
    };
    (t.version = "0.9.5"),
      (lunr = t),
      (t.utils = {}),
      (t.utils.warn = (function (e) {
        return function (t) {
          e.console && console.warn && console.warn(t);
        };
      })(this)),
      (t.utils.toString = function (e) {
        return void 0 === e || null === e ? "" : e.toString();
      }),
      (t.EventEmitter = function () {
        this.events = {};
      }),
      (t.EventEmitter.prototype.addListener = function () {
        var e = Array.prototype.slice.call(arguments),
          t = e.pop(),
          n = e;
        if ("function" != typeof t)
          throw new TypeError("last argument must be a function");
        n.forEach(function (e) {
          this.hasHandler(e) || (this.events[e] = []), this.events[e].push(t);
        }, this);
      }),
      (t.EventEmitter.prototype.removeListener = function (e, t) {
        if (this.hasHandler(e)) {
          var n = this.events[e].indexOf(t);
          -1 !== n &&
            (this.events[e].splice(n, 1),
            0 == this.events[e].length && delete this.events[e]);
        }
      }),
      (t.EventEmitter.prototype.emit = function (e) {
        if (this.hasHandler(e)) {
          var t = Array.prototype.slice.call(arguments, 1);
          this.events[e].forEach(function (e) {
            e.apply(void 0, t);
          }, this);
        }
      }),
      (t.EventEmitter.prototype.hasHandler = function (e) {
        return e in this.events;
      }),
      (t.tokenizer = function (e) {
        if (!arguments.length || null === e || void 0 === e) return [];
        if (Array.isArray(e)) {
          var n = e.filter(function (e) {
            return null === e || void 0 === e ? !1 : !0;
          });
          n = n.map(function (e) {
            return t.utils.toString(e).toLowerCase();
          });
          var i = [];
          return (
            n.forEach(function (e) {
              var n = e.split(t.tokenizer.seperator);
              i = i.concat(n);
            }, this),
            i
          );
        }
        return e.toString().trim().toLowerCase().split(t.tokenizer.seperator);
      }),
      (t.tokenizer.defaultSeperator = /[\s\-]+/),
      (t.tokenizer.seperator = t.tokenizer.defaultSeperator),
      (t.tokenizer.setSeperator = function (e) {
        null !== e &&
          void 0 !== e &&
          "object" == typeof e &&
          (t.tokenizer.seperator = e);
      }),
      (t.tokenizer.resetSeperator = function () {
        t.tokenizer.seperator = t.tokenizer.defaultSeperator;
      }),
      (t.tokenizer.getSeperator = function () {
        return t.tokenizer.seperator;
      }),
      (t.Pipeline = function () {
        this._queue = [];
      }),
      (t.Pipeline.registeredFunctions = {}),
      (t.Pipeline.registerFunction = function (e, n) {
        n in t.Pipeline.registeredFunctions &&
          t.utils.warn("Overwriting existing registered function: " + n),
          (e.label = n),
          (t.Pipeline.registeredFunctions[n] = e);
      }),
      (t.Pipeline.getRegisteredFunction = function (e) {
        return e in t.Pipeline.registeredFunctions != !0
          ? null
          : t.Pipeline.registeredFunctions[e];
      }),
      (t.Pipeline.warnIfFunctionNotRegistered = function (e) {
        var n = e.label && e.label in this.registeredFunctions;
        n ||
          t.utils.warn(
            "Function is not registered with pipeline. This may cause problems when serialising the index.\n",
            e
          );
      }),
      (t.Pipeline.load = function (e) {
        var n = new t.Pipeline();
        return (
          e.forEach(function (e) {
            var i = t.Pipeline.getRegisteredFunction(e);
            if (!i) throw new Error("Cannot load un-registered function: " + e);
            n.add(i);
          }),
          n
        );
      }),
      (t.Pipeline.prototype.add = function () {
        var e = Array.prototype.slice.call(arguments);
        e.forEach(function (e) {
          t.Pipeline.warnIfFunctionNotRegistered(e), this._queue.push(e);
        }, this);
      }),
      (t.Pipeline.prototype.after = function (e, n) {
        t.Pipeline.warnIfFunctionNotRegistered(n);
        var i = this._queue.indexOf(e);
        if (-1 === i) throw new Error("Cannot find existingFn");
        this._queue.splice(i + 1, 0, n);
      }),
      (t.Pipeline.prototype.before = function (e, n) {
        t.Pipeline.warnIfFunctionNotRegistered(n);
        var i = this._queue.indexOf(e);
        if (-1 === i) throw new Error("Cannot find existingFn");
        this._queue.splice(i, 0, n);
      }),
      (t.Pipeline.prototype.remove = function (e) {
        var t = this._queue.indexOf(e);
        -1 !== t && this._queue.splice(t, 1);
      }),
      (t.Pipeline.prototype.run = function (e) {
        for (
          var t = [], n = e.length, i = this._queue.length, o = 0;
          n > o;
          o++
        ) {
          for (
            var r = e[o], s = 0;
            i > s &&
            ((r = this._queue[s](r, o, e)), void 0 !== r && null !== r);
            s++
          );
          void 0 !== r && null !== r && t.push(r);
        }
        return t;
      }),
      (t.Pipeline.prototype.reset = function () {
        this._queue = [];
      }),
      (t.Pipeline.prototype.get = function () {
        return this._queue;
      }),
      (t.Pipeline.prototype.toJSON = function () {
        return this._queue.map(function (e) {
          return t.Pipeline.warnIfFunctionNotRegistered(e), e.label;
        });
      }),
      (t.Index = function () {
        (this._fields = []),
          (this._ref = "id"),
          (this.pipeline = new t.Pipeline()),
          (this.documentStore = new t.DocumentStore()),
          (this.index = {}),
          (this.eventEmitter = new t.EventEmitter()),
          (this._idfCache = {}),
          this.on(
            "add",
            "remove",
            "update",
            function () {
              this._idfCache = {};
            }.bind(this)
          );
      }),
      (t.Index.prototype.on = function () {
        var e = Array.prototype.slice.call(arguments);
        return this.eventEmitter.addListener.apply(this.eventEmitter, e);
      }),
      (t.Index.prototype.off = function (e, t) {
        return this.eventEmitter.removeListener(e, t);
      }),
      (t.Index.load = function (e) {
        e.version !== t.version &&
          t.utils.warn(
            "version mismatch: current " + t.version + " importing " + e.version
          );
        var n = new this();
        (n._fields = e.fields),
          (n._ref = e.ref),
          (n.documentStore = t.DocumentStore.load(e.documentStore)),
          (n.pipeline = t.Pipeline.load(e.pipeline)),
          (n.index = {});
        for (var i in e.index) n.index[i] = t.InvertedIndex.load(e.index[i]);
        return n;
      }),
      (t.Index.prototype.addField = function (e) {
        return (
          this._fields.push(e), (this.index[e] = new t.InvertedIndex()), this
        );
      }),
      (t.Index.prototype.setRef = function (e) {
        return (this._ref = e), this;
      }),
      (t.Index.prototype.saveDocument = function (e) {
        return (this.documentStore = new t.DocumentStore(e)), this;
      }),
      (t.Index.prototype.addDoc = function (e, n) {
        if (e) {
          var n = void 0 === n ? !0 : n,
            i = e[this._ref];
          this.documentStore.addDoc(i, e),
            this._fields.forEach(function (n) {
              var o = this.pipeline.run(t.tokenizer(e[n]));
              this.documentStore.addFieldLength(i, n, o.length);
              var r = {};
              o.forEach(function (e) {
                e in r ? (r[e] += 1) : (r[e] = 1);
              }, this);
              for (var s in r) {
                var u = r[s];
                (u = Math.sqrt(u)),
                  this.index[n].addToken(s, { ref: i, tf: u });
              }
            }, this),
            n && this.eventEmitter.emit("add", e, this);
        }
      }),
      (t.Index.prototype.removeDocByRef = function (e) {
        if (
          e &&
          this.documentStore.isDocStored() !== !1 &&
          this.documentStore.hasDoc(e)
        ) {
          var t = this.documentStore.getDoc(e);
          this.removeDoc(t, !1);
        }
      }),
      (t.Index.prototype.removeDoc = function (e, n) {
        if (e) {
          var n = void 0 === n ? !0 : n,
            i = e[this._ref];
          this.documentStore.hasDoc(i) &&
            (this.documentStore.removeDoc(i),
            this._fields.forEach(function (n) {
              var o = this.pipeline.run(t.tokenizer(e[n]));
              o.forEach(function (e) {
                this.index[n].removeToken(e, i);
              }, this);
            }, this),
            n && this.eventEmitter.emit("remove", e, this));
        }
      }),
      (t.Index.prototype.updateDoc = function (e, t) {
        var t = void 0 === t ? !0 : t;
        this.removeDocByRef(e[this._ref], !1),
          this.addDoc(e, !1),
          t && this.eventEmitter.emit("update", e, this);
      }),
      (t.Index.prototype.idf = function (e, t) {
        var n = "@" + t + "/" + e;
        if (Object.prototype.hasOwnProperty.call(this._idfCache, n))
          return this._idfCache[n];
        var i = this.index[t].getDocFreq(e),
          o = 1 + Math.log(this.documentStore.length / (i + 1));
        return (this._idfCache[n] = o), o;
      }),
      (t.Index.prototype.getFields = function () {
        return this._fields.slice();
      }),
      (t.Index.prototype.search = function (e, n) {
        if (!e) return [];
        e = "string" == typeof e ? { any: e } : JSON.parse(JSON.stringify(e));
        var i = null;
        null != n && (i = JSON.stringify(n));
        for (
          var o = new t.Configuration(i, this.getFields()).get(),
            r = {},
            s = Object.keys(e),
            u = 0;
          u < s.length;
          u++
        ) {
          var a = s[u];
          r[a] = this.pipeline.run(t.tokenizer(e[a]));
        }
        var l = {};
        for (var c in o) {
          var d = r[c] || r.any;
          if (d) {
            var f = this.fieldSearch(d, c, o),
              h = o[c].boost;
            for (var p in f) f[p] = f[p] * h;
            for (var p in f) p in l ? (l[p] += f[p]) : (l[p] = f[p]);
          }
        }
        var v,
          g = [];
        for (var p in l)
          (v = { ref: p, score: l[p] }),
            this.documentStore.hasDoc(p) &&
              (v.doc = this.documentStore.getDoc(p)),
            g.push(v);
        return (
          g.sort(function (e, t) {
            return t.score - e.score;
          }),
          g
        );
      }),
      (t.Index.prototype.fieldSearch = function (e, t, n) {
        var i = n[t].bool,
          o = n[t].expand,
          r = n[t].boost,
          s = null,
          u = {};
        return 0 !== r
          ? (e.forEach(function (e) {
              var n = [e];
              1 == o && (n = this.index[t].expandToken(e));
              var r = {};
              n.forEach(function (n) {
                var o = this.index[t].getDocs(n),
                  a = this.idf(n, t);
                if (s && "AND" == i) {
                  var l = {};
                  for (var c in s) c in o && (l[c] = o[c]);
                  o = l;
                }
                n == e && this.fieldSearchStats(u, n, o);
                for (var c in o) {
                  var d = this.index[t].getTermFrequency(n, c),
                    f = this.documentStore.getFieldLength(c, t),
                    h = 1;
                  0 != f && (h = 1 / Math.sqrt(f));
                  var p = 1;
                  n != e && (p = 0.15 * (1 - (n.length - e.length) / n.length));
                  var v = d * a * h * p;
                  c in r ? (r[c] += v) : (r[c] = v);
                }
              }, this),
                (s = this.mergeScores(s, r, i));
            }, this),
            (s = this.coordNorm(s, u, e.length)))
          : void 0;
      }),
      (t.Index.prototype.mergeScores = function (e, t, n) {
        if (!e) return t;
        if ("AND" == n) {
          var i = {};
          for (var o in t) o in e && (i[o] = e[o] + t[o]);
          return i;
        }
        for (var o in t) o in e ? (e[o] += t[o]) : (e[o] = t[o]);
        return e;
      }),
      (t.Index.prototype.fieldSearchStats = function (e, t, n) {
        for (var i in n) i in e ? e[i].push(t) : (e[i] = [t]);
      }),
      (t.Index.prototype.coordNorm = function (e, t, n) {
        for (var i in e)
          if (i in t) {
            var o = t[i].length;
            e[i] = (e[i] * o) / n;
          }
        return e;
      }),
      (t.Index.prototype.toJSON = function () {
        var e = {};
        return (
          this._fields.forEach(function (t) {
            e[t] = this.index[t].toJSON();
          }, this),
          {
            version: t.version,
            fields: this._fields,
            ref: this._ref,
            documentStore: this.documentStore.toJSON(),
            index: e,
            pipeline: this.pipeline.toJSON(),
          }
        );
      }),
      (t.Index.prototype.use = function (e) {
        var t = Array.prototype.slice.call(arguments, 1);
        t.unshift(this), e.apply(this, t);
      }),
      (t.DocumentStore = function (e) {
        (this._save = null === e || void 0 === e ? !0 : e),
          (this.docs = {}),
          (this.docInfo = {}),
          (this.length = 0);
      }),
      (t.DocumentStore.load = function (e) {
        var t = new this();
        return (
          (t.length = e.length),
          (t.docs = e.docs),
          (t.docInfo = e.docInfo),
          (t._save = e.save),
          t
        );
      }),
      (t.DocumentStore.prototype.isDocStored = function () {
        return this._save;
      }),
      (t.DocumentStore.prototype.addDoc = function (t, n) {
        this.hasDoc(t) || this.length++,
          (this.docs[t] = this._save === !0 ? e(n) : null);
      }),
      (t.DocumentStore.prototype.getDoc = function (e) {
        return this.hasDoc(e) === !1 ? null : this.docs[e];
      }),
      (t.DocumentStore.prototype.hasDoc = function (e) {
        return e in this.docs;
      }),
      (t.DocumentStore.prototype.removeDoc = function (e) {
        this.hasDoc(e) &&
          (delete this.docs[e], delete this.docInfo[e], this.length--);
      }),
      (t.DocumentStore.prototype.addFieldLength = function (e, t, n) {
        null !== e &&
          void 0 !== e &&
          0 != this.hasDoc(e) &&
          (this.docInfo[e] || (this.docInfo[e] = {}), (this.docInfo[e][t] = n));
      }),
      (t.DocumentStore.prototype.updateFieldLength = function (e, t, n) {
        null !== e &&
          void 0 !== e &&
          0 != this.hasDoc(e) &&
          this.addFieldLength(e, t, n);
      }),
      (t.DocumentStore.prototype.getFieldLength = function (e, t) {
        return null === e || void 0 === e
          ? 0
          : e in this.docs && t in this.docInfo[e]
          ? this.docInfo[e][t]
          : 0;
      }),
      (t.DocumentStore.prototype.toJSON = function () {
        return {
          docs: this.docs,
          docInfo: this.docInfo,
          length: this.length,
          save: this._save,
        };
      }),
      (t.stemmer = (function () {
        var e = {
            ational: "ate",
            tional: "tion",
            enci: "ence",
            anci: "ance",
            izer: "ize",
            bli: "ble",
            alli: "al",
            entli: "ent",
            eli: "e",
            ousli: "ous",
            ization: "ize",
            ation: "ate",
            ator: "ate",
            alism: "al",
            iveness: "ive",
            fulness: "ful",
            ousness: "ous",
            aliti: "al",
            iviti: "ive",
            biliti: "ble",
            logi: "log",
          },
          t = {
            icate: "ic",
            ative: "",
            alize: "al",
            iciti: "ic",
            ical: "ic",
            ful: "",
            ness: "",
          },
          n = "[^aeiou]",
          i = "[aeiouy]",
          o = n + "[^aeiouy]*",
          r = i + "[aeiou]*",
          s = "^(" + o + ")?" + r + o,
          u = "^(" + o + ")?" + r + o + "(" + r + ")?$",
          a = "^(" + o + ")?" + r + o + r + o,
          l = "^(" + o + ")?" + i,
          c = new RegExp(s),
          d = new RegExp(a),
          f = new RegExp(u),
          h = new RegExp(l),
          p = /^(.+?)(ss|i)es$/,
          v = /^(.+?)([^s])s$/,
          g = /^(.+?)eed$/,
          m = /^(.+?)(ed|ing)$/,
          y = /.$/,
          S = /(at|bl|iz)$/,
          x = new RegExp("([^aeiouylsz])\\1$"),
          w = new RegExp("^" + o + i + "[^aeiouwxy]$"),
          I = /^(.+?[^aeiou])y$/,
          b =
            /^(.+?)(ational|tional|enci|anci|izer|bli|alli|entli|eli|ousli|ization|ation|ator|alism|iveness|fulness|ousness|aliti|iviti|biliti|logi)$/,
          E = /^(.+?)(icate|ative|alize|iciti|ical|ful|ness)$/,
          D =
            /^(.+?)(al|ance|ence|er|ic|able|ible|ant|ement|ment|ent|ou|ism|ate|iti|ous|ive|ize)$/,
          F = /^(.+?)(s|t)(ion)$/,
          _ = /^(.+?)e$/,
          P = /ll$/,
          k = new RegExp("^" + o + i + "[^aeiouwxy]$"),
          z = function (n) {
            var i, o, r, s, u, a, l;
            if (n.length < 3) return n;
            if (
              ((r = n.substr(0, 1)),
              "y" == r && (n = r.toUpperCase() + n.substr(1)),
              (s = p),
              (u = v),
              s.test(n)
                ? (n = n.replace(s, "$1$2"))
                : u.test(n) && (n = n.replace(u, "$1$2")),
              (s = g),
              (u = m),
              s.test(n))
            ) {
              var z = s.exec(n);
              (s = c), s.test(z[1]) && ((s = y), (n = n.replace(s, "")));
            } else if (u.test(n)) {
              var z = u.exec(n);
              (i = z[1]),
                (u = h),
                u.test(i) &&
                  ((n = i),
                  (u = S),
                  (a = x),
                  (l = w),
                  u.test(n)
                    ? (n += "e")
                    : a.test(n)
                    ? ((s = y), (n = n.replace(s, "")))
                    : l.test(n) && (n += "e"));
            }
            if (((s = I), s.test(n))) {
              var z = s.exec(n);
              (i = z[1]), (n = i + "i");
            }
            if (((s = b), s.test(n))) {
              var z = s.exec(n);
              (i = z[1]), (o = z[2]), (s = c), s.test(i) && (n = i + e[o]);
            }
            if (((s = E), s.test(n))) {
              var z = s.exec(n);
              (i = z[1]), (o = z[2]), (s = c), s.test(i) && (n = i + t[o]);
            }
            if (((s = D), (u = F), s.test(n))) {
              var z = s.exec(n);
              (i = z[1]), (s = d), s.test(i) && (n = i);
            } else if (u.test(n)) {
              var z = u.exec(n);
              (i = z[1] + z[2]), (u = d), u.test(i) && (n = i);
            }
            if (((s = _), s.test(n))) {
              var z = s.exec(n);
              (i = z[1]),
                (s = d),
                (u = f),
                (a = k),
                (s.test(i) || (u.test(i) && !a.test(i))) && (n = i);
            }
            return (
              (s = P),
              (u = d),
              s.test(n) && u.test(n) && ((s = y), (n = n.replace(s, ""))),
              "y" == r && (n = r.toLowerCase() + n.substr(1)),
              n
            );
          };
        return z;
      })()),
      t.Pipeline.registerFunction(t.stemmer, "stemmer"),
      (t.stopWordFilter = function (e) {
        return e && t.stopWordFilter.stopWords[e] !== !0 ? e : void 0;
      }),
      (t.clearStopWords = function () {
        t.stopWordFilter.stopWords = {};
      }),
      (t.addStopWords = function (e) {
        null != e &&
          Array.isArray(e) !== !1 &&
          e.forEach(function (e) {
            t.stopWordFilter.stopWords[e] = !0;
          }, this);
      }),
      (t.resetStopWords = function () {
        t.stopWordFilter.stopWords = t.defaultStopWords;
      }),
      (t.defaultStopWords = {
        "": !0,
        a: !0,
        able: !0,
        about: !0,
        across: !0,
        after: !0,
        all: !0,
        almost: !0,
        also: !0,
        am: !0,
        among: !0,
        an: !0,
        and: !0,
        any: !0,
        are: !0,
        as: !0,
        at: !0,
        be: !0,
        because: !0,
        been: !0,
        but: !0,
        by: !0,
        can: !0,
        cannot: !0,
        could: !0,
        dear: !0,
        did: !0,
        do: !0,
        does: !0,
        either: !0,
        else: !0,
        ever: !0,
        every: !0,
        for: !0,
        from: !0,
        get: !0,
        got: !0,
        had: !0,
        has: !0,
        have: !0,
        he: !0,
        her: !0,
        hers: !0,
        him: !0,
        his: !0,
        how: !0,
        however: !0,
        i: !0,
        if: !0,
        in: !0,
        into: !0,
        is: !0,
        it: !0,
        its: !0,
        just: !0,
        least: !0,
        let: !0,
        like: !0,
        likely: !0,
        may: !0,
        me: !0,
        might: !0,
        most: !0,
        must: !0,
        my: !0,
        neither: !0,
        no: !0,
        nor: !0,
        not: !0,
        of: !0,
        off: !0,
        often: !0,
        on: !0,
        only: !0,
        or: !0,
        other: !0,
        our: !0,
        own: !0,
        rather: !0,
        said: !0,
        say: !0,
        says: !0,
        she: !0,
        should: !0,
        since: !0,
        so: !0,
        some: !0,
        than: !0,
        that: !0,
        the: !0,
        their: !0,
        them: !0,
        then: !0,
        there: !0,
        these: !0,
        they: !0,
        this: !0,
        tis: !0,
        to: !0,
        too: !0,
        twas: !0,
        us: !0,
        wants: !0,
        was: !0,
        we: !0,
        were: !0,
        what: !0,
        when: !0,
        where: !0,
        which: !0,
        while: !0,
        who: !0,
        whom: !0,
        why: !0,
        will: !0,
        with: !0,
        would: !0,
        yet: !0,
        you: !0,
        your: !0,
      }),
      (t.stopWordFilter.stopWords = t.defaultStopWords),
      t.Pipeline.registerFunction(t.stopWordFilter, "stopWordFilter"),
      (t.trimmer = function (e) {
        if (null === e || void 0 === e)
          throw new Error("token should not be undefined");
        return e.replace(/^\W+/, "").replace(/\W+$/, "");
      }),
      t.Pipeline.registerFunction(t.trimmer, "trimmer"),
      (t.InvertedIndex = function () {
        this.root = { docs: {}, df: 0 };
      }),
      (t.InvertedIndex.load = function (e) {
        var t = new this();
        return (t.root = e.root), t;
      }),
      (t.InvertedIndex.prototype.addToken = function (e, t, n) {
        for (var n = n || this.root, i = 0; i <= e.length - 1; ) {
          var o = e[i];
          o in n || (n[o] = { docs: {}, df: 0 }), (i += 1), (n = n[o]);
        }
        var r = t.ref;
        n.docs[r]
          ? (n.docs[r] = { tf: t.tf })
          : ((n.docs[r] = { tf: t.tf }), (n.df += 1));
      }),
      (t.InvertedIndex.prototype.hasToken = function (e) {
        if (!e) return !1;
        for (var t = this.root, n = 0; n < e.length; n++) {
          if (!t[e[n]]) return !1;
          t = t[e[n]];
        }
        return !0;
      }),
      (t.InvertedIndex.prototype.getNode = function (e) {
        if (!e) return null;
        for (var t = this.root, n = 0; n < e.length; n++) {
          if (!t[e[n]]) return null;
          t = t[e[n]];
        }
        return t;
      }),
      (t.InvertedIndex.prototype.getDocs = function (e) {
        var t = this.getNode(e);
        return null == t ? {} : t.docs;
      }),
      (t.InvertedIndex.prototype.getTermFrequency = function (e, t) {
        var n = this.getNode(e);
        return null == n ? 0 : t in n.docs ? n.docs[t].tf : 0;
      }),
      (t.InvertedIndex.prototype.getDocFreq = function (e) {
        var t = this.getNode(e);
        return null == t ? 0 : t.df;
      }),
      (t.InvertedIndex.prototype.removeToken = function (e, t) {
        if (e) {
          var n = this.getNode(e);
          null != n && t in n.docs && (delete n.docs[t], (n.df -= 1));
        }
      }),
      (t.InvertedIndex.prototype.expandToken = function (e, t, n) {
        if (null == e || "" == e) return [];
        var t = t || [];
        if (void 0 == n && ((n = this.getNode(e)), null == n)) return t;
        n.df > 0 && t.push(e);
        for (var i in n)
          "docs" !== i && "df" !== i && this.expandToken(e + i, t, n[i]);
        return t;
      }),
      (t.InvertedIndex.prototype.toJSON = function () {
        return { root: this.root };
      }),
      (t.Configuration = function (e, n) {
        var e = e || "";
        if (void 0 == n || null == n)
          throw new Error("fields should not be null");
        this.config = {};
        var i;
        try {
          (i = JSON.parse(e)), this.buildUserConfig(i, n);
        } catch (o) {
          t.utils.warn(
            "user configuration parse failed, will use default configuration"
          ),
            this.buildDefaultConfig(n);
        }
      }),
      (t.Configuration.prototype.buildDefaultConfig = function (e) {
        this.reset(),
          e.forEach(function (e) {
            this.config[e] = { boost: 1, bool: "OR", expand: !1 };
          }, this);
      }),
      (t.Configuration.prototype.buildUserConfig = function (e, n) {
        var i = "OR",
          o = !1;
        if (
          (this.reset(),
          "bool" in e && (i = e.bool || i),
          "expand" in e && (o = e.expand || o),
          "fields" in e)
        )
          for (var r in e.fields)
            if (n.indexOf(r) > -1) {
              var s = e.fields[r],
                u = o;
              void 0 != s.expand && (u = s.expand),
                (this.config[r] = {
                  boost: s.boost || 0 === s.boost ? s.boost : 1,
                  bool: s.bool || i,
                  expand: u,
                });
            } else
              t.utils.warn(
                "field name in user configuration not found in index instance fields"
              );
        else this.addAllFields2UserConfig(i, o, n);
      }),
      (t.Configuration.prototype.addAllFields2UserConfig = function (e, t, n) {
        n.forEach(function (n) {
          this.config[n] = { boost: 1, bool: e, expand: t };
        }, this);
      }),
      (t.Configuration.prototype.get = function () {
        return this.config;
      }),
      (t.Configuration.prototype.reset = function () {
        this.config = {};
      }),
      (lunr.SortedSet = function () {
        (this.length = 0), (this.elements = []);
      }),
      (lunr.SortedSet.load = function (e) {
        var t = new this();
        return (t.elements = e), (t.length = e.length), t;
      }),
      (lunr.SortedSet.prototype.add = function () {
        var e, t;
        for (e = 0; e < arguments.length; e++)
          (t = arguments[e]),
            ~this.indexOf(t) || this.elements.splice(this.locationFor(t), 0, t);
        this.length = this.elements.length;
      }),
      (lunr.SortedSet.prototype.toArray = function () {
        return this.elements.slice();
      }),
      (lunr.SortedSet.prototype.map = function (e, t) {
        return this.elements.map(e, t);
      }),
      (lunr.SortedSet.prototype.forEach = function (e, t) {
        return this.elements.forEach(e, t);
      }),
      (lunr.SortedSet.prototype.indexOf = function (e) {
        for (
          var t = 0,
            n = this.elements.length,
            i = n - t,
            o = t + Math.floor(i / 2),
            r = this.elements[o];
          i > 1;

        ) {
          if (r === e) return o;
          e > r && (t = o),
            r > e && (n = o),
            (i = n - t),
            (o = t + Math.floor(i / 2)),
            (r = this.elements[o]);
        }
        return r === e ? o : -1;
      }),
      (lunr.SortedSet.prototype.locationFor = function (e) {
        for (
          var t = 0,
            n = this.elements.length,
            i = n - t,
            o = t + Math.floor(i / 2),
            r = this.elements[o];
          i > 1;

        )
          e > r && (t = o),
            r > e && (n = o),
            (i = n - t),
            (o = t + Math.floor(i / 2)),
            (r = this.elements[o]);
        return r > e ? o : e > r ? o + 1 : void 0;
      }),
      (lunr.SortedSet.prototype.intersect = function (e) {
        for (
          var t = new lunr.SortedSet(),
            n = 0,
            i = 0,
            o = this.length,
            r = e.length,
            s = this.elements,
            u = e.elements;
          ;

        ) {
          if (n > o - 1 || i > r - 1) break;
          s[n] !== u[i]
            ? s[n] < u[i]
              ? n++
              : s[n] > u[i] && i++
            : (t.add(s[n]), n++, i++);
        }
        return t;
      }),
      (lunr.SortedSet.prototype.clone = function () {
        var e = new lunr.SortedSet();
        return (e.elements = this.toArray()), (e.length = e.elements.length), e;
      }),
      (lunr.SortedSet.prototype.union = function (e) {
        var t, n, i;
        this.length >= e.length ? ((t = this), (n = e)) : ((t = e), (n = this)),
          (i = t.clone());
        for (var o = 0, r = n.toArray(); o < r.length; o++) i.add(r[o]);
        return i;
      }),
      (lunr.SortedSet.prototype.toJSON = function () {
        return this.toArray();
      }),
      (function (e, t) {
        "function" == typeof define && define.amd
          ? define(t)
          : "object" == typeof exports
          ? (module.exports = t())
          : (e.elasticlunr = t());
      })(this, function () {
        return t;
      });
  })();
  /** pdoc search index */ const docs = [
    {
      fullname: "lactationcurve",
      modulename: "lactationcurve",
      kind: "module",
      doc: "<p></p>\n",
    },
    {
      fullname: "lactationcurve.lactation_curve_characterstics",
      modulename: "lactationcurve.lactation_curve_characterstics",
      kind: "module",
      doc: "<p></p>\n",
    },
    {
      fullname:
        "lactationcurve.lactation_curve_characterstics.lactation_curve_characteristic_function",
      modulename: "lactationcurve.lactation_curve_characterstics",
      qualname: "lactation_curve_characteristic_function",
      kind: "function",
      doc: "<p>Formula to extract lactation curve characteristics from the different mathematical models</p>\n\n<p>Input:\n model (Str): type of model you wish to extract characteristics from. Options: milkbot, wood, wilmink, ali_schaeffer, fischer, brody, sikka, nelder, dhanoa, emmans, hayashi, rook, dijkstra, prasad.\n characteristic (Str): characteristic you wish to extract, options are time_to_peak, peak_yield (both based on where the derivate of the function equals zero) and cumulative_milk_yield (based on the integral over 305 days).</p>\n\n<p>Output: equation for characteristic</p>\n",
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">model</span><span class="o">=</span><span class="s1">&#39;wood&#39;</span>, </span><span class="param"><span class="n">characteristic</span><span class="o">=</span><span class="kc">None</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname:
        "lactationcurve.lactation_curve_characterstics.calculate_characteristic",
      modulename: "lactationcurve.lactation_curve_characterstics",
      qualname: "calculate_characteristic",
      kind: "function",
      doc: "<p>Evaluate a lactation curve characteristic from a set of milkrecordings.</p>\n\n<p>Inputs:\n    dim (Int): days in milk\n    milkrecordings (Float): milk recording of the test day in kg\n    characteristic (String): characteristic you want to calculate, choose between time_to_peak, peak_yield_cumulative_milk_yield.\n    fitting (String): way of fitting the data, options: 'frequentist' or 'Bayesian'.</p>\n\n<pre><code>Extra input for Bayesian fitting:\nkey (String): key to use the fitting API\nparity (Int): parity of the cow, all above 3 are considered 3\nbreed (String): breed of the cow H = Holstein, J = Jersey\ncontinent (String): continent of the cow, options USA, EU and defined by Chen et al.\n\noutput: float of desired characteristic\n</code></pre>\n",
      signature:
        '<span class="signature pdoc-code multiline">(<span class="param">\t<span class="n">dim</span>,</span><span class="param">\t<span class="n">milkrecordings</span>,</span><span class="param">\t<span class="n">model</span>,</span><span class="param">\t<span class="n">characteristic</span>,</span><span class="param">\t<span class="n">fitting</span><span class="o">=</span><span class="s1">&#39;frequentist&#39;</span>,</span><span class="param">\t<span class="n">key</span><span class="o">=</span><span class="kc">None</span>,</span><span class="param">\t<span class="n">parity</span><span class="o">=</span><span class="mi">3</span>,</span><span class="param">\t<span class="n">breed</span><span class="o">=</span><span class="s1">&#39;H&#39;</span>,</span><span class="param">\t<span class="n">continent</span><span class="o">=</span><span class="s1">&#39;USA&#39;</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname:
        "lactationcurve.lactation_curve_characterstics.persistency_wood",
      modulename: "lactationcurve.lactation_curve_characterstics",
      qualname: "persistency_wood",
      kind: "function",
      doc: "<p></p>\n",
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">b</span>, </span><span class="param"><span class="n">c</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname:
        "lactationcurve.lactation_curve_characterstics.persistency_milkbot",
      modulename: "lactationcurve.lactation_curve_characterstics",
      qualname: "persistency_milkbot",
      kind: "function",
      doc: "<p></p>\n",
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">d</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname: "lactationcurve.lactation_curve_fitting",
      modulename: "lactationcurve.lactation_curve_fitting",
      kind: "module",
      doc: "<p></p>\n",
    },
    {
      fullname: "lactationcurve.lactation_curve_fitting.milkbot_model",
      modulename: "lactationcurve.lactation_curve_fitting",
      qualname: "milkbot_model",
      kind: "function",
      doc: "<p>MilkBot lactation curve model</p>\n\n<p>Input variables:\n    t = time since calving in days (DIM)\n    a = scale, the overall level of milk production\n    b = ramp, governs the rate of the rise\n    in early lactation\n    c = offset is a small (usually insignificant) correction for time between calving and the theoretical start of lactation\n    d = decay is the rate of exponential decline, most apparent in late lactation</p>\n\n<p>output: milk yield at time t</p>\n",
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">t</span>, </span><span class="param"><span class="n">a</span>, </span><span class="param"><span class="n">b</span>, </span><span class="param"><span class="n">c</span>, </span><span class="param"><span class="n">d</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname: "lactationcurve.lactation_curve_fitting.wood_model",
      modulename: "lactationcurve.lactation_curve_fitting",
      qualname: "wood_model",
      kind: "function",
      doc: "<p>Wood Lactation curve model\nInput variables:\n    t = time since calving in days (DIM)\n    a,b,c = parameters Wood model (numerical)</p>\n\n<p>Output: milk yield at time t</p>\n",
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">t</span>, </span><span class="param"><span class="n">a</span>, </span><span class="param"><span class="n">b</span>, </span><span class="param"><span class="n">c</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname: "lactationcurve.lactation_curve_fitting.wilmink_model",
      modulename: "lactationcurve.lactation_curve_fitting",
      qualname: "wilmink_model",
      kind: "function",
      doc: "<p>Wilmink Lactation curve model\nInput variables:\n    t = time since calving in days (DIM)\n    a,b,c = parameters Wilmink model, (numerical)\n    k = parameter Wilmink function (numerical), with default value -0.05\nOutput: milk yield at time t</p>\n",
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">t</span>, </span><span class="param"><span class="n">a</span>, </span><span class="param"><span class="n">b</span>, </span><span class="param"><span class="n">c</span>, </span><span class="param"><span class="n">k</span><span class="o">=-</span><span class="mf">0.05</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname: "lactationcurve.lactation_curve_fitting.ali_schaeffer_model",
      modulename: "lactationcurve.lactation_curve_fitting",
      qualname: "ali_schaeffer_model",
      kind: "function",
      doc: "<p>Ali &amp; Schaeffer Lactation curve model\nInput variables:\n    t = time since calving in days (DIM)\n    a,b,c,d,k = parameters Ali &amp; Schaeffer model (numerical)</p>\n\n<p>Output: milk yield at time t</p>\n",
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">t</span>, </span><span class="param"><span class="n">a</span>, </span><span class="param"><span class="n">b</span>, </span><span class="param"><span class="n">c</span>, </span><span class="param"><span class="n">d</span>, </span><span class="param"><span class="n">k</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname: "lactationcurve.lactation_curve_fitting.fischer_model",
      modulename: "lactationcurve.lactation_curve_fitting",
      qualname: "fischer_model",
      kind: "function",
      doc: "<p>Fischer Lactation curve model\nInput variables:\n    t = time since calving in days (DIM)\n    a,b,c,d,k = parameters Wood model (numerical)</p>\n\n<p>Output: milk yield at time t</p>\n",
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">t</span>, </span><span class="param"><span class="n">a</span>, </span><span class="param"><span class="n">b</span>, </span><span class="param"><span class="n">c</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname: "lactationcurve.lactation_curve_fitting.brody_model",
      modulename: "lactationcurve.lactation_curve_fitting",
      qualname: "brody_model",
      kind: "function",
      doc: "<p>Brody Lactation curve model\nInput variables:\n    t = time since calving in days (DIM)\n    a,k = parameters Brody model (numerical)</p>\n\n<p>Output: milk yield at time t</p>\n",
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">t</span>, </span><span class="param"><span class="n">a</span>, </span><span class="param"><span class="n">k</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname: "lactationcurve.lactation_curve_fitting.sikka_model",
      modulename: "lactationcurve.lactation_curve_fitting",
      qualname: "sikka_model",
      kind: "function",
      doc: "<p>Sikka Lactation curve model\nInput variables:\nt = time since calving in days (DIM)\na,b,c= parameters Sikka model (numerical)</p>\n\n<p>Output: milk yield at time t</p>\n",
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">t</span>, </span><span class="param"><span class="n">a</span>, </span><span class="param"><span class="n">b</span>, </span><span class="param"><span class="n">c</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname: "lactationcurve.lactation_curve_fitting.nelder_model",
      modulename: "lactationcurve.lactation_curve_fitting",
      qualname: "nelder_model",
      kind: "function",
      doc: "<p>Nelder Lactation curve model\nInput variables:\nt = time since calving in days (DIM)\na,b,c= parameters Nelder model (numerical)</p>\n\n<p>Output: milk yield at time t</p>\n",
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">t</span>, </span><span class="param"><span class="n">a</span>, </span><span class="param"><span class="n">b</span>, </span><span class="param"><span class="n">c</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname: "lactationcurve.lactation_curve_fitting.dhanoa_model",
      modulename: "lactationcurve.lactation_curve_fitting",
      qualname: "dhanoa_model",
      kind: "function",
      doc: "<p>Dhanoa Lactation curve model\nInput variables:\nt = time since calving in days (DIM)\na,b,c= parameters Dhanoa model (numerical)</p>\n\n<p>Output: milk yield at time t</p>\n",
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">t</span>, </span><span class="param"><span class="n">a</span>, </span><span class="param"><span class="n">b</span>, </span><span class="param"><span class="n">c</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname: "lactationcurve.lactation_curve_fitting.emmans_model",
      modulename: "lactationcurve.lactation_curve_fitting",
      qualname: "emmans_model",
      kind: "function",
      doc: "<p>Emmans Lactation curve model\nInput variables:\nt = time since calving in days (DIM)\na,b,c,d = parameters Emmans model (numerical)</p>\n\n<p>Output: milk yield at time t</p>\n",
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">t</span>, </span><span class="param"><span class="n">a</span>, </span><span class="param"><span class="n">b</span>, </span><span class="param"><span class="n">c</span>, </span><span class="param"><span class="n">d</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname: "lactationcurve.lactation_curve_fitting.hayashi_model",
      modulename: "lactationcurve.lactation_curve_fitting",
      qualname: "hayashi_model",
      kind: "function",
      doc: "<p>Hayashi Lactation curve model\nInput variables:\nt = time since calving in days (DIM)\na,b,c,d = parameters Hayashi model (numerical)</p>\n\n<p>Output: milk yield at time t</p>\n",
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">t</span>, </span><span class="param"><span class="n">a</span>, </span><span class="param"><span class="n">b</span>, </span><span class="param"><span class="n">c</span>, </span><span class="param"><span class="n">d</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname: "lactationcurve.lactation_curve_fitting.rook_model",
      modulename: "lactationcurve.lactation_curve_fitting",
      qualname: "rook_model",
      kind: "function",
      doc: "<p>Rook Lactation curve model\nInput variables:\nt = time since calving in days (DIM)\na,b,c,d = parameters Rook model (numerical)</p>\n\n<p>Output: milk yield at time t</p>\n",
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">t</span>, </span><span class="param"><span class="n">a</span>, </span><span class="param"><span class="n">b</span>, </span><span class="param"><span class="n">c</span>, </span><span class="param"><span class="n">d</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname: "lactationcurve.lactation_curve_fitting.dijkstra_model",
      modulename: "lactationcurve.lactation_curve_fitting",
      qualname: "dijkstra_model",
      kind: "function",
      doc: "<p>Dijkstra Lactation curve model\nInput variables:\nt = time since calving in days (DIM)\na,b,c,d = parameters Dijkstra model (numerical)</p>\n\n<p>Output: milk yield at time t</p>\n",
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">t</span>, </span><span class="param"><span class="n">a</span>, </span><span class="param"><span class="n">b</span>, </span><span class="param"><span class="n">c</span>, </span><span class="param"><span class="n">d</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname: "lactationcurve.lactation_curve_fitting.prasad_model",
      modulename: "lactationcurve.lactation_curve_fitting",
      qualname: "prasad_model",
      kind: "function",
      doc: "<p>Prasad Lactation curve model\nInput variables:\nt = time since calving in days (DIM)\na,b,c,d = parameters Prasad model (numerical)</p>\n\n<p>Output: milk yield at time t</p>\n",
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">t</span>, </span><span class="param"><span class="n">a</span>, </span><span class="param"><span class="n">b</span>, </span><span class="param"><span class="n">c</span>, </span><span class="param"><span class="n">d</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname: "lactationcurve.lactation_curve_fitting.wood_objective",
      modulename: "lactationcurve.lactation_curve_fitting",
      qualname: "wood_objective",
      kind: "function",
      doc: "<p></p>\n",
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">par</span>, </span><span class="param"><span class="n">x</span>, </span><span class="param"><span class="n">y</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname: "lactationcurve.lactation_curve_fitting.milkbot_objective",
      modulename: "lactationcurve.lactation_curve_fitting",
      qualname: "milkbot_objective",
      kind: "function",
      doc: "<p></p>\n",
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">par</span>, </span><span class="param"><span class="n">x</span>, </span><span class="param"><span class="n">y</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname: "lactationcurve.lactation_curve_fitting.fit_lactation_curve",
      modulename: "lactationcurve.lactation_curve_fitting",
      qualname: "fit_lactation_curve",
      kind: "function",
      doc: "<p>Fit lactation data to a lactation curve model using sklearn minimize or curvefit or the MilkBot Bayesian fitting API\nInput variables:\ndim (Int) = list of dim\nmilkrecordings (Float) = list of milk recordings\nmodel (Str)= type of pre-defined model function, default = Wood model. Model name is all lowercase\nfitting (Str) = method of fitting the data to the curve using optimalization either frequentist(curvefit/minimize) or Bayesian, default is frequentist. In the current version only for the MilkBot model Bayesian fitting is available.</p>\n\n<p>Only relevant if fitting is Bayesian\n    breed (Str): either H or J, H = Holstein and is the default, J = Jersey\n    Parity (Int): lactionnumber, default = 3, all parities &gt;= 3 are considered as one group\n    Continent (Str): source of the default priors, can be USA (default), EU or from Chen et al.\n    key (Str): key for the milkbot API  Mandatory to use fitting API. For a free API Key, contact Jim Ehrlich jehrlich@MilkBot.com</p>\n\n<p>Output (list of floats): list of milk yield for range 1-305 or until the maximum day in milk when this is more than 305</p>\n",
      signature:
        '<span class="signature pdoc-code multiline">(<span class="param">\t<span class="n">dim</span>,</span><span class="param">\t<span class="n">milkrecordings</span>,</span><span class="param">\t<span class="n">model</span><span class="o">=</span><span class="s1">&#39;wood&#39;</span>,</span><span class="param">\t<span class="n">fitting</span><span class="o">=</span><span class="s1">&#39;frequentist&#39;</span>,</span><span class="param">\t<span class="n">breed</span><span class="o">=</span><span class="s1">&#39;H&#39;</span>,</span><span class="param">\t<span class="n">parity</span><span class="o">=</span><span class="mi">3</span>,</span><span class="param">\t<span class="n">continent</span><span class="o">=</span><span class="s1">&#39;USA&#39;</span>,</span><span class="param">\t<span class="n">key</span><span class="o">=</span><span class="kc">None</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname: "lactationcurve.lactation_curve_fitting.get_lc_parameters",
      modulename: "lactationcurve.lactation_curve_fitting",
      qualname: "get_lc_parameters",
      kind: "function",
      doc: "<p>Fit lactation data to a lactation curve model and return the model parameters using frequetist statistics: sklearn minimize and curvefit\nInput variables:\ndim (int) = list of dim\nmilkrecordings (float) = list of milk recordings\nmodel (str) = type of pre-defined model function, default = Wood model. Model name is all lowercase</p>\n\n<p>output: parameters as np.float in alphabetic order</p>\n",
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">dim</span>, </span><span class="param"><span class="n">milkrecordings</span>, </span><span class="param"><span class="n">model</span><span class="o">=</span><span class="s1">&#39;wood&#39;</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname: "lactationcurve.lactation_curve_fitting.get_milkbot_data",
      modulename: "lactationcurve.lactation_curve_fitting",
      qualname: "get_milkbot_data",
      kind: "function",
      doc: "<p>Functions to call the API of MilkBot\nInput variables: json string of the lactation with the needed metadata (parity, breed, dim, my)\nOutput json string with lactationcurve parameters of the fitted MilkBot model</p>\n",
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">row</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname:
        "lactationcurve.lactation_curve_fitting.bayesian_fit_milkbot_single_lactation",
      modulename: "lactationcurve.lactation_curve_fitting",
      qualname: "bayesian_fit_milkbot_single_lactation",
      kind: "function",
      doc: '<p>Milkbot fitted using the MilkBot API (<a href="https://api.milkbot.com/#section/MilkBot-Fitting">https://api.milkbot.com/#section/MilkBot-Fitting</a>)</p>\n\n<p>Parameters:\n    dim (list[int]): Days in milk.\n    milkrecordings (list[float]): Milk yield recordings.\n    key (str): API key for MilkBot.\n    parity (int): Cow parity (default=3).\n    continent (str): Region for prior selection (USA, EU or priors made by Chen et al.)</p>\n\n<p>Returns:\n    dict: Fitted parameters and metrics.</p>\n',
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">dim</span>, </span><span class="param"><span class="n">milkrecordings</span>, </span><span class="param"><span class="n">key</span>, </span><span class="param"><span class="n">parity</span><span class="o">=</span><span class="mi">3</span>, </span><span class="param"><span class="n">breed</span><span class="o">=</span><span class="s1">&#39;H&#39;</span>, </span><span class="param"><span class="n">continent</span><span class="o">=</span><span class="s1">&#39;USA&#39;</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname: "lactationcurve.lactation_curve_fitting.get_milkbot_priors",
      modulename: "lactationcurve.lactation_curve_fitting",
      qualname: "get_milkbot_priors",
      kind: "function",
      doc: "<p>Get priors from the MilkBot API</p>\n\n<p>input features:\nkey (Str): milkbot key, for a free API Key, contact Jim Ehrlich jehrlich@MilkBot.com</p>\n",
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">key</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname: "lactationcurve.lactation_curve_fitting.get_cow_priors",
      modulename: "lactationcurve.lactation_curve_fitting",
      qualname: "get_cow_priors",
      kind: "function",
      doc: "<p>Fetch priors from the MilkBot API for a given continent breed and parity.</p>\n\n<p>Input features:\ncontinent (Str): Region for prior selection (USA, EU or priors made by Chen et al.)\nbreed (Str): 'H' for Holstein, 'J' for Jersey\nparity (Int): parity (1, 2, 3+), all parities &gt;= 3 are grouped together\nkey (Str): milkbot key, for a free API Key, contact Jim Ehrlich jehrlich@MilkBot.com</p>\n\n<p>Output features:\npriors for Bayesian fitting in a json string</p>\n",
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">continent</span>, </span><span class="param"><span class="n">breed</span><span class="p">:</span> <span class="nb">str</span>, </span><span class="param"><span class="n">parity</span><span class="p">:</span> <span class="nb">int</span>, </span><span class="param"><span class="n">key</span><span class="p">:</span> <span class="nb">str</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname: "lactationcurve.TheTestIntervalMethodICAR",
      modulename: "lactationcurve.TheTestIntervalMethodICAR",
      kind: "module",
      doc: "<p></p>\n",
    },
    {
      fullname: "lactationcurve.TheTestIntervalMethodICAR.test_interval_method",
      modulename: "lactationcurve.TheTestIntervalMethodICAR",
      qualname: "test_interval_method",
      kind: "function",
      doc: "<p>Calculate the total 305-day milk yield using the trapezoidal rule\nfor interim days, and linear projection for start and end beyond the sampling period.</p>\n\n<p>Parameters:\n    df (DataFrame): Input DataFrame\n    days_in_milk_col (str): Optional override for the DaysInMilk column\n    milking_yield_col (str): Optional override for the MilkingYield column\n    test_id_col (str): Optional override for the TestId column\n    default_test_id (any): If TestId column is missing, create it with this value</p>\n\n<p>Returns:\n    panda dataframe with the columns TestId, Total 305-day milk yield.</p>\n",
      signature:
        '<span class="signature pdoc-code multiline">(<span class="param">\t<span class="n">df</span>,</span><span class="param">\t<span class="n">days_in_milk_col</span><span class="o">=</span><span class="kc">None</span>,</span><span class="param">\t<span class="n">milking_yield_col</span><span class="o">=</span><span class="kc">None</span>,</span><span class="param">\t<span class="n">test_id_col</span><span class="o">=</span><span class="kc">None</span>,</span><span class="param">\t<span class="n">default_test_id</span><span class="o">=</span><span class="mi">1</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      kind: "module",
      doc: "<p></p>\n",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.data_path",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "data_path",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "WindowsPath(&#x27;C:/Users/Meike van Leerdam/lactation-curves/lactationcurve/tests/TestData/MRtestFile.csv&#x27;)",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.df",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "df",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "       BirthDate  DaysInMilk  Parity  MilkingYield   TestDate  TestId CalvingDate  AgeAtCalvingDays  AgeAtCalvingMonths AgeClass CalvingSeason\n0     2017-08-26          27       1          23.6 2019-08-20    3781  2019-07-24               697           22.897503    22-24       Jun-Jul\n1     2017-08-26          64       1          23.1 2019-09-26    3781  2019-07-24               697           22.897503    22-24       Jun-Jul\n2     2017-08-26          98       1          23.7 2019-10-30    3781  2019-07-24               697           22.897503    22-24       Jun-Jul\n3     2017-08-26         132       1          24.1 2019-12-03    3781  2019-07-24               697           22.897503    22-24       Jun-Jul\n4     2017-08-26         174       1          25.9 2020-01-14    3781  2019-07-24               697           22.897503    22-24       Jun-Jul\n...          ...         ...     ...           ...        ...     ...         ...               ...                 ...      ...           ...\n33340 2016-01-21          13       4          14.1 2022-01-26    3518  2022-01-13              2184           71.747700    69-92       Dec-Jan\n33341 2016-01-21          54       4          14.2 2022-03-08    3518  2022-01-13              2184           71.747700    69-92       Dec-Jan\n33342 2016-01-21          90       4          10.9 2022-04-13    3518  2022-01-13              2184           71.747700    69-92       Dec-Jan\n33343 2016-01-21         125       4           9.6 2022-05-18    3518  2022-01-13              2184           71.747700    69-92       Dec-Jan\n33344 2016-01-21         162       4           6.1 2022-06-24    3518  2022-01-13              2184           71.747700    69-92       Dec-Jan\n\n[32617 rows x 11 columns]",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.bin_edges",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "bin_edges",
      kind: "variable",
      doc: "<p></p>\n",
      default_value: "[22, 25, 28, 33, 38, 45, 57, 69, 93, 105, inf]",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.labels",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "labels",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "[&#x27;22-24&#x27;, &#x27;25-27&#x27;, &#x27;28-32&#x27;, &#x27;33-37&#x27;, &#x27;38-44&#x27;, &#x27;45-56&#x27;, &#x27;57-68&#x27;, &#x27;69-92&#x27;, &#x27;93-104&#x27;, &#x27;105+&#x27;]",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.season_labels",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "season_labels",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "[&#x27;Aug-Sep&#x27;, &#x27;Oct-Nov&#x27;, &#x27;Dec-Jan&#x27;, &#x27;Feb-Mar&#x27;, &#x27;Apr-May&#x27;, &#x27;Jun-Jul&#x27;]",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.shifted_month",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "shifted_month",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "0        11\n1        11\n2        11\n3        11\n4        11\n         ..\n33341     5\n33342     5\n33343     5\n33344     5\n33345     8\nName: CalvingDate, Length: 33346, dtype: int32",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.counts",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "counts",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "TestId\n0       7\n1       6\n2       7\n3       7\n4       7\n       ..\n4315    3\n4316    3\n4317    3\n4322    1\n4324    1\nName: DaysInMilk, Length: 4259, dtype: int64",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.valid_ids",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "valid_ids",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "Index([   0,    1,    2,    3,    4,    5,    6,    7,    8,    9,\n       ...\n       4307, 4308, 4309, 4310, 4311, 4313, 4314, 4315, 4316, 4317],\n      dtype=&#x27;int64&#x27;, name=&#x27;TestId&#x27;, length=4069)",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.grid",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "grid",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "[10, 30, 50, 70, 90, 110, 130, 150, 170, 190, 210, 230, 250, 270, 290]",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.interpolate_to_grid",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "interpolate_to_grid",
      kind: "function",
      doc: "<p></p>\n",
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">group</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.df_grid",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "df_grid",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "       TestId  GridDay  MilkYieldInterp AgeClass CalvingSeason\n0           0       10        35.400000     105+       Dec-Jan\n1           0       30        37.595122     105+       Dec-Jan\n2           0       50        39.790244     105+       Dec-Jan\n3           0       70        35.914634     105+       Dec-Jan\n4           0       90        31.719512     105+       Dec-Jan\n...       ...      ...              ...      ...           ...\n61030    4317      210         6.975510    22-24       Feb-Mar\n61031    4317      230         4.322449    22-24       Feb-Mar\n61032    4317      250         1.669388    22-24       Feb-Mar\n61033    4317      270        -0.983673    22-24       Feb-Mar\n61034    4317      290        -3.636735    22-24       Feb-Mar\n\n[61035 rows x 5 columns]",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.model",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "model",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "&lt;statsmodels.regression.linear_model.RegressionResultsWrapper object&gt;",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.ageclass_coefs",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "ageclass_coefs",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "C(AgeClass)[T.22-24]    -2.734804\nC(AgeClass)[T.25-27]    -2.211606\nC(AgeClass)[T.28-32]    -0.982162\nC(AgeClass)[T.33-37]     1.532096\nC(AgeClass)[T.38-44]     3.697147\nC(AgeClass)[T.45-56]     3.627801\nC(AgeClass)[T.57-68]     4.004640\nC(AgeClass)[T.69-92]     3.536557\nC(AgeClass)[T.93-104]    2.569699\ndtype: float64",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.calving_season_coefs",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "calving_season_coefs",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "C(CalvingSeason)[T.Aug-Sep]   -1.486395\nC(CalvingSeason)[T.Dec-Jan]    0.737406\nC(CalvingSeason)[T.Feb-Mar]    0.285529\nC(CalvingSeason)[T.Jun-Jul]   -1.700071\nC(CalvingSeason)[T.Oct-Nov]    0.413327\ndtype: float64",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.results",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "results",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "[{&#x27;GridDay&#x27;: np.int64(10), &#x27;AgeClass&#x27;: &#x27;22-24&#x27;, &#x27;AdjMeanYield&#x27;: np.float64(25.631057250541204)}, {&#x27;GridDay&#x27;: np.int64(10), &#x27;AgeClass&#x27;: &#x27;105+&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(11.384254089934624)}, {&#x27;GridDay&#x27;: np.int64(10), &#x27;AgeClass&#x27;: &#x27;45-56&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(13.273780898337446)}, {&#x27;GridDay&#x27;: np.int64(10), &#x27;AgeClass&#x27;: &#x27;57-68&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(13.93014028574745)}, {&#x27;GridDay&#x27;: np.int64(10), &#x27;AgeClass&#x27;: &#x27;69-92&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(13.558790596228954)}, {&#x27;GridDay&#x27;: np.int64(10), &#x27;AgeClass&#x27;: &#x27;93-104&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(11.963274329366529)}, {&#x27;GridDay&#x27;: np.int64(10), &#x27;AgeClass&#x27;: &#x27;38-44&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(12.275593459833383)}, {&#x27;GridDay&#x27;: np.int64(10), &#x27;AgeClass&#x27;: &#x27;33-37&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(9.845250892293606)}, {&#x27;GridDay&#x27;: np.int64(10), &#x27;AgeClass&#x27;: &#x27;28-32&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(2.388178895500342)}, {&#x27;GridDay&#x27;: np.int64(10), &#x27;AgeClass&#x27;: &#x27;25-27&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(0.5926975231609941)}, {&#x27;GridDay&#x27;: np.int64(30), &#x27;AgeClass&#x27;: &#x27;22-24&#x27;, &#x27;AdjMeanYield&#x27;: np.float64(27.78191136451184)}, {&#x27;GridDay&#x27;: np.int64(30), &#x27;AgeClass&#x27;: &#x27;105+&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(10.969280318822365)}, {&#x27;GridDay&#x27;: np.int64(30), &#x27;AgeClass&#x27;: &#x27;45-56&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(12.94877448593799)}, {&#x27;GridDay&#x27;: np.int64(30), &#x27;AgeClass&#x27;: &#x27;57-68&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(13.906219849690428)}, {&#x27;GridDay&#x27;: np.int64(30), &#x27;AgeClass&#x27;: &#x27;69-92&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(13.541315283121444)}, {&#x27;GridDay&#x27;: np.int64(30), &#x27;AgeClass&#x27;: &#x27;93-104&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(11.945496028533707)}, {&#x27;GridDay&#x27;: np.int64(30), &#x27;AgeClass&#x27;: &#x27;38-44&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(12.020462858152401)}, {&#x27;GridDay&#x27;: np.int64(30), &#x27;AgeClass&#x27;: &#x27;33-37&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(9.167200596369641)}, {&#x27;GridDay&#x27;: np.int64(30), &#x27;AgeClass&#x27;: &#x27;28-32&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(2.273027867109361)}, {&#x27;GridDay&#x27;: np.int64(30), &#x27;AgeClass&#x27;: &#x27;25-27&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(0.5342546848959637)}, {&#x27;GridDay&#x27;: np.int64(50), &#x27;AgeClass&#x27;: &#x27;22-24&#x27;, &#x27;AdjMeanYield&#x27;: np.float64(29.393460663507295)}, {&#x27;GridDay&#x27;: np.int64(50), &#x27;AgeClass&#x27;: &#x27;105+&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(10.44461832469051)}, {&#x27;GridDay&#x27;: np.int64(50), &#x27;AgeClass&#x27;: &#x27;45-56&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(12.40357476243453)}, {&#x27;GridDay&#x27;: np.int64(50), &#x27;AgeClass&#x27;: &#x27;57-68&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(13.617570202559401)}, {&#x27;GridDay&#x27;: np.int64(50), &#x27;AgeClass&#x27;: &#x27;69-92&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(13.207029832590596)}, {&#x27;GridDay&#x27;: np.int64(50), &#x27;AgeClass&#x27;: &#x27;93-104&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(11.382594306435788)}, {&#x27;GridDay&#x27;: np.int64(50), &#x27;AgeClass&#x27;: &#x27;38-44&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(11.342160057397495)}, {&#x27;GridDay&#x27;: np.int64(50), &#x27;AgeClass&#x27;: &#x27;33-37&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(8.398592757764668)}, {&#x27;GridDay&#x27;: np.int64(50), &#x27;AgeClass&#x27;: &#x27;28-32&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(2.190873136649529)}, {&#x27;GridDay&#x27;: np.int64(50), &#x27;AgeClass&#x27;: &#x27;25-27&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(0.6190506999525427)}, {&#x27;GridDay&#x27;: np.int64(70), &#x27;AgeClass&#x27;: &#x27;22-24&#x27;, &#x27;AdjMeanYield&#x27;: np.float64(29.55281518126297)}, {&#x27;GridDay&#x27;: np.int64(70), &#x27;AgeClass&#x27;: &#x27;105+&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(9.176827598155727)}, {&#x27;GridDay&#x27;: np.int64(70), &#x27;AgeClass&#x27;: &#x27;45-56&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(11.170803189139198)}, {&#x27;GridDay&#x27;: np.int64(70), &#x27;AgeClass&#x27;: &#x27;57-68&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(12.182629113055267)}, {&#x27;GridDay&#x27;: np.int64(70), &#x27;AgeClass&#x27;: &#x27;69-92&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(12.03602341594591)}, {&#x27;GridDay&#x27;: np.int64(70), &#x27;AgeClass&#x27;: &#x27;93-104&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(9.89791499547454)}, {&#x27;GridDay&#x27;: np.int64(70), &#x27;AgeClass&#x27;: &#x27;38-44&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(9.994134096010068)}, {&#x27;GridDay&#x27;: np.int64(70), &#x27;AgeClass&#x27;: &#x27;33-37&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(7.279537766928177)}, {&#x27;GridDay&#x27;: np.int64(70), &#x27;AgeClass&#x27;: &#x27;28-32&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(2.1157327109945014)}, {&#x27;GridDay&#x27;: np.int64(70), &#x27;AgeClass&#x27;: &#x27;25-27&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(0.5956101301865704)}, {&#x27;GridDay&#x27;: np.int64(90), &#x27;AgeClass&#x27;: &#x27;22-24&#x27;, &#x27;AdjMeanYield&#x27;: np.float64(29.012321507944026)}, {&#x27;GridDay&#x27;: np.int64(90), &#x27;AgeClass&#x27;: &#x27;105+&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(7.615962073692482)}, {&#x27;GridDay&#x27;: np.int64(90), &#x27;AgeClass&#x27;: &#x27;45-56&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(9.830708658384733)}, {&#x27;GridDay&#x27;: np.int64(90), &#x27;AgeClass&#x27;: &#x27;57-68&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(10.644794489811455)}, {&#x27;GridDay&#x27;: np.int64(90), &#x27;AgeClass&#x27;: &#x27;69-92&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(10.690711843373052)}, {&#x27;GridDay&#x27;: np.int64(90), &#x27;AgeClass&#x27;: &#x27;93-104&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(8.766034604004421)}, {&#x27;GridDay&#x27;: np.int64(90), &#x27;AgeClass&#x27;: &#x27;38-44&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(8.996297216781104)}, {&#x27;GridDay&#x27;: np.int64(90), &#x27;AgeClass&#x27;: &#x27;33-37&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(6.339109238738136)}, {&#x27;GridDay&#x27;: np.int64(90), &#x27;AgeClass&#x27;: &#x27;28-32&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(2.2650070130578546)}, {&#x27;GridDay&#x27;: np.int64(90), &#x27;AgeClass&#x27;: &#x27;25-27&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(0.683209706799785)}, {&#x27;GridDay&#x27;: np.int64(110), &#x27;AgeClass&#x27;: &#x27;22-24&#x27;, &#x27;AdjMeanYield&#x27;: np.float64(28.20728186314234)}, {&#x27;GridDay&#x27;: np.int64(110), &#x27;AgeClass&#x27;: &#x27;105+&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(5.757167733283828)}, {&#x27;GridDay&#x27;: np.int64(110), &#x27;AgeClass&#x27;: &#x27;45-56&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(8.593757825838535)}, {&#x27;GridDay&#x27;: np.int64(110), &#x27;AgeClass&#x27;: &#x27;57-68&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(9.269189133914114)}, {&#x27;GridDay&#x27;: np.int64(110), &#x27;AgeClass&#x27;: &#x27;69-92&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(9.285520479437961)}, {&#x27;GridDay&#x27;: np.int64(110), &#x27;AgeClass&#x27;: &#x27;93-104&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(7.451750770863226)}, {&#x27;GridDay&#x27;: np.int64(110), &#x27;AgeClass&#x27;: &#x27;38-44&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(8.103982254247937)}, {&#x27;GridDay&#x27;: np.int64(110), &#x27;AgeClass&#x27;: &#x27;33-37&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(5.5981042769214815)}, {&#x27;GridDay&#x27;: np.int64(110), &#x27;AgeClass&#x27;: &#x27;28-32&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(2.428688008677508)}, {&#x27;GridDay&#x27;: np.int64(110), &#x27;AgeClass&#x27;: &#x27;25-27&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(0.7396297323725207)}, {&#x27;GridDay&#x27;: np.int64(130), &#x27;AgeClass&#x27;: &#x27;22-24&#x27;, &#x27;AdjMeanYield&#x27;: np.float64(27.43323330455429)}, {&#x27;GridDay&#x27;: np.int64(130), &#x27;AgeClass&#x27;: &#x27;105+&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(3.8602059346425057)}, {&#x27;GridDay&#x27;: np.int64(130), &#x27;AgeClass&#x27;: &#x27;45-56&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(7.510958496865013)}, {&#x27;GridDay&#x27;: np.int64(130), &#x27;AgeClass&#x27;: &#x27;57-68&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(7.9374319633588835)}, {&#x27;GridDay&#x27;: np.int64(130), &#x27;AgeClass&#x27;: &#x27;69-92&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(7.848683964388826)}, {&#x27;GridDay&#x27;: np.int64(130), &#x27;AgeClass&#x27;: &#x27;93-104&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(6.302926580750917)}, {&#x27;GridDay&#x27;: np.int64(130), &#x27;AgeClass&#x27;: &#x27;38-44&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(7.1224340607706145)}, {&#x27;GridDay&#x27;: np.int64(130), &#x27;AgeClass&#x27;: &#x27;33-37&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(4.774932933046961)}, {&#x27;GridDay&#x27;: np.int64(130), &#x27;AgeClass&#x27;: &#x27;28-32&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(2.054181845895034)}, {&#x27;GridDay&#x27;: np.int64(130), &#x27;AgeClass&#x27;: &#x27;25-27&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(0.6390694722574911)}, {&#x27;GridDay&#x27;: np.int64(150), &#x27;AgeClass&#x27;: &#x27;22-24&#x27;, &#x27;AdjMeanYield&#x27;: np.float64(26.692475115423246)}, {&#x27;GridDay&#x27;: np.int64(150), &#x27;AgeClass&#x27;: &#x27;105+&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(2.2949221013387557)}, {&#x27;GridDay&#x27;: np.int64(150), &#x27;AgeClass&#x27;: &#x27;45-56&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(6.301359141670215)}, {&#x27;GridDay&#x27;: np.int64(150), &#x27;AgeClass&#x27;: &#x27;57-68&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(6.662502759656485)}, {&#x27;GridDay&#x27;: np.int64(150), &#x27;AgeClass&#x27;: &#x27;69-92&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(6.306820480642561)}, {&#x27;GridDay&#x27;: np.int64(150), &#x27;AgeClass&#x27;: &#x27;93-104&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(5.363610788176305)}, {&#x27;GridDay&#x27;: np.int64(150), &#x27;AgeClass&#x27;: &#x27;38-44&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(6.150509516609937)}, {&#x27;GridDay&#x27;: np.int64(150), &#x27;AgeClass&#x27;: &#x27;33-37&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(3.963753814549384)}, {&#x27;GridDay&#x27;: np.int64(150), &#x27;AgeClass&#x27;: &#x27;28-32&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(1.7254274784932273)}, {&#x27;GridDay&#x27;: np.int64(150), &#x27;AgeClass&#x27;: &#x27;25-27&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(0.5649287326069747)}, {&#x27;GridDay&#x27;: np.int64(170), &#x27;AgeClass&#x27;: &#x27;22-24&#x27;, &#x27;AdjMeanYield&#x27;: np.float64(25.909927242045512)}, {&#x27;GridDay&#x27;: np.int64(170), &#x27;AgeClass&#x27;: &#x27;105+&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(1.0427413412559121)}, {&#x27;GridDay&#x27;: np.int64(170), &#x27;AgeClass&#x27;: &#x27;45-56&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(5.0913213821393795)}, {&#x27;GridDay&#x27;: np.int64(170), &#x27;AgeClass&#x27;: &#x27;57-68&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(5.421776241404311)}, {&#x27;GridDay&#x27;: np.int64(170), &#x27;AgeClass&#x27;: &#x27;69-92&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(4.841608825450599)}, {&#x27;GridDay&#x27;: np.int64(170), &#x27;AgeClass&#x27;: &#x27;93-104&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(4.234885389947496)}, {&#x27;GridDay&#x27;: np.int64(170), &#x27;AgeClass&#x27;: &#x27;38-44&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(5.324016784985845)}, {&#x27;GridDay&#x27;: np.int64(170), &#x27;AgeClass&#x27;: &#x27;33-37&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(3.3822375573280348)}, {&#x27;GridDay&#x27;: np.int64(170), &#x27;AgeClass&#x27;: &#x27;28-32&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(1.434032051406334)}, {&#x27;GridDay&#x27;: np.int64(170), &#x27;AgeClass&#x27;: &#x27;25-27&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(0.5196782217572047)}, {&#x27;GridDay&#x27;: np.int64(190), &#x27;AgeClass&#x27;: &#x27;22-24&#x27;, &#x27;AdjMeanYield&#x27;: np.float64(25.18355933930522)}, {&#x27;GridDay&#x27;: np.int64(190), &#x27;AgeClass&#x27;: &#x27;105+&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(-0.22661657547068376)}, {&#x27;GridDay&#x27;: np.int64(190), &#x27;AgeClass&#x27;: &#x27;45-56&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(3.9899141989254825)}, {&#x27;GridDay&#x27;: np.int64(190), &#x27;AgeClass&#x27;: &#x27;57-68&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(4.288768161496195)}, {&#x27;GridDay&#x27;: np.int64(190), &#x27;AgeClass&#x27;: &#x27;69-92&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(3.549396857815274)}, {&#x27;GridDay&#x27;: np.int64(190), &#x27;AgeClass&#x27;: &#x27;93-104&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(3.0244141688064796)}, {&#x27;GridDay&#x27;: np.int64(190), &#x27;AgeClass&#x27;: &#x27;38-44&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(4.580332138316236)}, {&#x27;GridDay&#x27;: np.int64(190), &#x27;AgeClass&#x27;: &#x27;33-37&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(2.8081570429114167)}, {&#x27;GridDay&#x27;: np.int64(190), &#x27;AgeClass&#x27;: &#x27;28-32&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(1.2973133245367794)}, {&#x27;GridDay&#x27;: np.int64(190), &#x27;AgeClass&#x27;: &#x27;25-27&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(0.4560478732572198)}, {&#x27;GridDay&#x27;: np.int64(210), &#x27;AgeClass&#x27;: &#x27;22-24&#x27;, &#x27;AdjMeanYield&#x27;: np.float64(24.483510132759616)}, {&#x27;GridDay&#x27;: np.int64(210), &#x27;AgeClass&#x27;: &#x27;105+&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(-1.6794415991382656)}, {&#x27;GridDay&#x27;: np.int64(210), &#x27;AgeClass&#x27;: &#x27;45-56&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(2.967282790502585)}, {&#x27;GridDay&#x27;: np.int64(210), &#x27;AgeClass&#x27;: &#x27;57-68&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(3.1465162231901647)}, {&#x27;GridDay&#x27;: np.int64(210), &#x27;AgeClass&#x27;: &#x27;69-92&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(2.2712793222062255)}, {&#x27;GridDay&#x27;: np.int64(210), &#x27;AgeClass&#x27;: &#x27;93-104&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(1.883934412576328)}, {&#x27;GridDay&#x27;: np.int64(210), &#x27;AgeClass&#x27;: &#x27;38-44&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(3.856086738639926)}, {&#x27;GridDay&#x27;: np.int64(210), &#x27;AgeClass&#x27;: &#x27;33-37&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(2.0924957434638523)}, {&#x27;GridDay&#x27;: np.int64(210), &#x27;AgeClass&#x27;: &#x27;28-32&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(1.2853721199467447)}, {&#x27;GridDay&#x27;: np.int64(210), &#x27;AgeClass&#x27;: &#x27;25-27&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(0.4301019942446108)}, {&#x27;GridDay&#x27;: np.int64(230), &#x27;AgeClass&#x27;: &#x27;22-24&#x27;, &#x27;AdjMeanYield&#x27;: np.float64(23.697751158769048)}, {&#x27;GridDay&#x27;: np.int64(230), &#x27;AgeClass&#x27;: &#x27;105+&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(-3.05351348667635)}, {&#x27;GridDay&#x27;: np.int64(230), &#x27;AgeClass&#x27;: &#x27;45-56&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(1.952682822025112)}, {&#x27;GridDay&#x27;: np.int64(230), &#x27;AgeClass&#x27;: &#x27;57-68&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(1.9177805689534586)}, {&#x27;GridDay&#x27;: np.int64(230), &#x27;AgeClass&#x27;: &#x27;69-92&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(1.0202931870088596)}, {&#x27;GridDay&#x27;: np.int64(230), &#x27;AgeClass&#x27;: &#x27;93-104&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(0.894714415259876)}, {&#x27;GridDay&#x27;: np.int64(230), &#x27;AgeClass&#x27;: &#x27;38-44&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(3.005623960409254)}, {&#x27;GridDay&#x27;: np.int64(230), &#x27;AgeClass&#x27;: &#x27;33-37&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(1.3696562840013078)}, {&#x27;GridDay&#x27;: np.int64(230), &#x27;AgeClass&#x27;: &#x27;28-32&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(1.3120381415083722)}, {&#x27;GridDay&#x27;: np.int64(230), &#x27;AgeClass&#x27;: &#x27;25-27&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(0.41778262653698406)}, {&#x27;GridDay&#x27;: np.int64(250), &#x27;AgeClass&#x27;: &#x27;22-24&#x27;, &#x27;AdjMeanYield&#x27;: np.float64(22.83902979598037)}, {&#x27;GridDay&#x27;: np.int64(250), &#x27;AgeClass&#x27;: &#x27;105+&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(-4.242013636450926)}, {&#x27;GridDay&#x27;: np.int64(250), &#x27;AgeClass&#x27;: &#x27;45-56&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(0.9185783688457914)}, {&#x27;GridDay&#x27;: np.int64(250), &#x27;AgeClass&#x27;: &#x27;57-68&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(0.6840558425949064)}, {&#x27;GridDay&#x27;: np.int64(250), &#x27;AgeClass&#x27;: &#x27;69-92&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(-0.20209355322548445)}, {&#x27;GridDay&#x27;: np.int64(250), &#x27;AgeClass&#x27;: &#x27;93-104&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(-0.06684991774755905)}, {&#x27;GridDay&#x27;: np.int64(250), &#x27;AgeClass&#x27;: &#x27;38-44&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(2.105316172384377)}, {&#x27;GridDay&#x27;: np.int64(250), &#x27;AgeClass&#x27;: &#x27;33-37&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(0.5347018439530749)}, {&#x27;GridDay&#x27;: np.int64(250), &#x27;AgeClass&#x27;: &#x27;28-32&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(1.2136140619229585)}, {&#x27;GridDay&#x27;: np.int64(250), &#x27;AgeClass&#x27;: &#x27;25-27&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(0.40562341665750584)}, {&#x27;GridDay&#x27;: np.int64(270), &#x27;AgeClass&#x27;: &#x27;22-24&#x27;, &#x27;AdjMeanYield&#x27;: np.float64(21.87266773514703)}, {&#x27;GridDay&#x27;: np.int64(270), &#x27;AgeClass&#x27;: &#x27;105+&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(-5.520663775233047)}, {&#x27;GridDay&#x27;: np.int64(270), &#x27;AgeClass&#x27;: &#x27;45-56&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(-0.19544556456419815)}, {&#x27;GridDay&#x27;: np.int64(270), &#x27;AgeClass&#x27;: &#x27;57-68&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(-0.5839341454243085)}, {&#x27;GridDay&#x27;: np.int64(270), &#x27;AgeClass&#x27;: &#x27;69-92&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(-1.3750401459927348)}, {&#x27;GridDay&#x27;: np.int64(270), &#x27;AgeClass&#x27;: &#x27;93-104&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(-1.141576468874694)}, {&#x27;GridDay&#x27;: np.int64(270), &#x27;AgeClass&#x27;: &#x27;38-44&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(1.2450276562317322)}, {&#x27;GridDay&#x27;: np.int64(270), &#x27;AgeClass&#x27;: &#x27;33-37&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(-0.33337559312719545)}, {&#x27;GridDay&#x27;: np.int64(270), &#x27;AgeClass&#x27;: &#x27;28-32&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(1.168361806050352)}, {&#x27;GridDay&#x27;: np.int64(270), &#x27;AgeClass&#x27;: &#x27;25-27&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(0.33531351837909873)}, {&#x27;GridDay&#x27;: np.int64(290), &#x27;AgeClass&#x27;: &#x27;22-24&#x27;, &#x27;AdjMeanYield&#x27;: np.float64(20.842115643344847)}, {&#x27;GridDay&#x27;: np.int64(290), &#x27;AgeClass&#x27;: &#x27;105+&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(-6.801666071270943)}, {&#x27;GridDay&#x27;: np.int64(290), &#x27;AgeClass&#x27;: &#x27;45-56&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(-1.3189712945941936)}, {&#x27;GridDay&#x27;: np.int64(290), &#x27;AgeClass&#x27;: &#x27;57-68&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(-1.933774883057147)}, {&#x27;GridDay&#x27;: np.int64(290), &#x27;AgeClass&#x27;: &#x27;69-92&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(-2.5099202711518833)}, {&#x27;GridDay&#x27;: np.int64(290), &#x27;AgeClass&#x27;: &#x27;93-104&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(-2.3355740685066513)}, {&#x27;GridDay&#x27;: np.int64(290), &#x27;AgeClass&#x27;: &#x27;38-44&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(0.3572900970232794)}, {&#x27;GridDay&#x27;: np.int64(290), &#x27;AgeClass&#x27;: &#x27;33-37&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(-1.216846013150442)}, {&#x27;GridDay&#x27;: np.int64(290), &#x27;AgeClass&#x27;: &#x27;28-32&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(1.137792921510659)}, {&#x27;GridDay&#x27;: np.int64(290), &#x27;AgeClass&#x27;: &#x27;25-27&#x27;, &#x27;AdjMeanYieldDiff&#x27;: np.float64(0.3149763229282438)}]",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.df_adj",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "df_adj",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "     GridDay AgeClass  AdjMeanYield  AdjMeanYieldDiff\n1         10     105+           NaN         11.384254\n0         10    22-24     25.631057               NaN\n9         10    25-27           NaN          0.592698\n8         10    28-32           NaN          2.388179\n7         10    33-37           NaN          9.845251\n..       ...      ...           ...               ...\n146      290    38-44           NaN          0.357290\n142      290    45-56           NaN         -1.318971\n143      290    57-68           NaN         -1.933775\n144      290    69-92           NaN         -2.509920\n145      290   93-104           NaN         -2.335574\n\n[150 rows x 4 columns]",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.lc_model",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "lc_model",
      kind: "function",
      doc: "<p></p>\n",
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">x</span>, </span><span class="param"><span class="n">a</span>, </span><span class="param"><span class="n">b</span>, </span><span class="param"><span class="n">c</span>, </span><span class="param"><span class="n">d</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.age_class_one",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "age_class_one",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "     GridDay AgeClass  AdjMeanYield  AdjMeanYieldDiff\n0         10    22-24     25.631057               NaN\n10        30    22-24     27.781911               NaN\n20        50    22-24     29.393461               NaN\n30        70    22-24     29.552815               NaN\n40        90    22-24     29.012322               NaN\n50       110    22-24     28.207282               NaN\n60       130    22-24     27.433233               NaN\n70       150    22-24     26.692475               NaN\n80       170    22-24     25.909927               NaN\n90       190    22-24     25.183559               NaN\n100      210    22-24     24.483510               NaN\n110      230    22-24     23.697751               NaN\n120      250    22-24     22.839030               NaN\n130      270    22-24     21.872668               NaN\n140      290    22-24     20.842116               NaN",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.x",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "x",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "array([ 10,  30,  50,  70,  90, 110, 130, 150, 170, 190, 210, 230, 250,\n       270, 290])",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.y",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "y",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "array([25.63105725, 27.78191136, 29.39346066, 29.55281518, 29.01232151,\n       28.20728186, 27.4332333 , 26.69247512, 25.90992724, 25.18355934,\n       24.48351013, 23.69775116, 22.8390298 , 21.87266774, 20.84211564])",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.y_fit",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "y_fit",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "array([25.41686796, 28.47934315, 29.25626198, 29.17006026, 28.74402288,\n       28.1706556 , 27.52077732, 26.82044087, 26.07923053, 25.30067219,\n       24.48606292, 23.63587991, 22.7502987 , 21.82938387, 20.87315916])",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.dif_model",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "dif_model",
      kind: "function",
      doc: "<p></p>\n",
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">x</span>, </span><span class="param"><span class="n">a</span>, </span><span class="param"><span class="n">b</span>, </span><span class="param"><span class="n">c</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.age_class_not_one",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "age_class_not_one",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "     GridDay AgeClass  AdjMeanYield  AdjMeanYieldDiff\n1         10     105+           NaN         11.384254\n9         10    25-27           NaN          0.592698\n8         10    28-32           NaN          2.388179\n7         10    33-37           NaN          9.845251\n6         10    38-44           NaN         12.275593\n..       ...      ...           ...               ...\n146      290    38-44           NaN          0.357290\n142      290    45-56           NaN         -1.318971\n143      290    57-68           NaN         -1.933775\n144      290    69-92           NaN         -2.509920\n145      290   93-104           NaN         -2.335574\n\n[135 rows x 4 columns]",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.a_t",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "a_t",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "{&#x27;105+&#x27;: np.float64(13.843155865025556), &#x27;25-27&#x27;: np.float64(0.7761099135899937), &#x27;28-32&#x27;: np.float64(2.6248619134010784), &#x27;33-37&#x27;: np.float64(9.921534101735357), &#x27;38-44&#x27;: np.float64(13.117795058471836), &#x27;45-56&#x27;: np.float64(15.012984229301013), &#x27;57-68&#x27;: np.float64(16.516900841800062), &#x27;69-92&#x27;: np.float64(16.634357244191545), &#x27;93-104&#x27;: np.float64(13.900449859880698)}",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.b_t",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "b_t",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "{&#x27;105+&#x27;: np.float64(-0.07288580391609739), &#x27;25-27&#x27;: np.float64(-0.001532388394054113), &#x27;28-32&#x27;: np.float64(-0.005652160567578695), &#x27;33-37&#x27;: np.float64(-0.0379971105425077), &#x27;38-44&#x27;: np.float64(-0.04441663369982123), &#x27;45-56&#x27;: np.float64(-0.05689986150905444), &#x27;57-68&#x27;: np.float64(-0.06386878789985252), &#x27;69-92&#x27;: np.float64(-0.06738709057248315), &#x27;93-104&#x27;: np.float64(-0.05643448201602657)}",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.c_t",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "c_t",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "{&#x27;105+&#x27;: np.float64(-2.743270382109658), &#x27;25-27&#x27;: np.float64(-0.36038979156057643), &#x27;28-32&#x27;: np.float64(-0.38136480059853806), &#x27;33-37&#x27;: np.float64(0.7024328687239476), &#x27;38-44&#x27;: np.float64(-0.36500963995522223), &#x27;45-56&#x27;: np.float64(-1.804027165809339), &#x27;57-68&#x27;: np.float64(-3.0818357488324826), &#x27;69-92&#x27;: np.float64(-3.9853222293678536), &#x27;93-104&#x27;: np.float64(-2.0443753045966906)}",
    },
    {
      fullname:
        "lactationcurve.WilminkCorrectionFactors.age_classes_parity_one_two",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "age_classes_parity_one_two",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "[&#x27;25-27&#x27;, &#x27;28-32&#x27;, &#x27;33-37&#x27;, &#x27;38-44&#x27;]",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.model_param_t_low_par",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "model_param_t_low_par",
      kind: "function",
      doc: "<p></p>\n",
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">t</span>, </span><span class="param"><span class="n">p</span>, </span><span class="param"><span class="n">q</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.subset_dict",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "subset_dict",
      kind: "function",
      doc: "<p></p>\n",
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">d</span>, </span><span class="param"><span class="n">keys_to_include</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.a_par_one_two",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "a_par_one_two",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "[np.float64(0.7761099135899937), np.float64(2.6248619134010784), np.float64(9.921534101735357), np.float64(13.117795058471836)]",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.b_par_one_two",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "b_par_one_two",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "[np.float64(-0.001532388394054113), np.float64(-0.005652160567578695), np.float64(-0.0379971105425077), np.float64(-0.04441663369982123)]",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.c_par_one_two",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "c_par_one_two",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "[np.float64(-0.36038979156057643), np.float64(-0.38136480059853806), np.float64(0.7024328687239476), np.float64(-0.36500963995522223)]",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.averages",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "averages",
      kind: "variable",
      doc: "<p></p>\n",
      default_value: "[50.5, 62.5, 80.5, 98.5, 105]",
    },
    {
      fullname:
        "lactationcurve.WilminkCorrectionFactors.age_classes_parity_three",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "age_classes_parity_three",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "[&#x27;45-56&#x27;, &#x27;57-68&#x27;, &#x27;69-92&#x27;, &#x27;93-104&#x27;, &#x27;105+&#x27;]",
    },
    {
      fullname:
        "lactationcurve.WilminkCorrectionFactors.model_param_t_high_par",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "model_param_t_high_par",
      kind: "function",
      doc: "<p></p>\n",
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">t</span>, </span><span class="param"><span class="n">p</span>, </span><span class="param"><span class="n">q</span>, </span><span class="param"><span class="n">r</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.a_par_three",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "a_par_three",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "[np.float64(15.012984229301013), np.float64(16.516900841800062), np.float64(16.634357244191545), np.float64(13.900449859880698), np.float64(13.843155865025556)]",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.b_par_three",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "b_par_three",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "[np.float64(-0.05689986150905444), np.float64(-0.06386878789985252), np.float64(-0.06738709057248315), np.float64(-0.05643448201602657), np.float64(-0.07288580391609739)]",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.c_par_three",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "c_par_three",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "[np.float64(-1.804027165809339), np.float64(-3.0818357488324826), np.float64(-3.9853222293678536), np.float64(-2.0443753045966906), np.float64(-2.743270382109658)]",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.correction_factor_age",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "correction_factor_age",
      kind: "function",
      doc: "<p>Apply selfmade multiplicative correction to a milkyield at days in milk (t), based on a correction.</p>\n\n<p>input:\nx (int)= x the age of the animal at calving that was measured in months\nbase (int): age at calving in month of referenc animal &gt; lactation you want to correct to\nt (int) = days in milk of milk measurement</p>\n\n<p>output (numpy float): multiplicative correction factor</p>\n",
      signature:
        '<span class="signature pdoc-code condensed">(<span class="param"><span class="n">x</span>, </span><span class="param"><span class="n">base</span>, </span><span class="param"><span class="n">t</span></span><span class="return-annotation">):</span></span>',
      funcdef: "def",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.season_dict",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "season_dict",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "{&#x27;Aug-Sep&#x27;: -1.48639529134209, &#x27;Dec-Jan&#x27;: 0.7374057334145495, &#x27;Feb-Mar&#x27;: 0.28552867477443217, &#x27;Jun-Jul&#x27;: -1.700071281552897, &#x27;Oct-Nov&#x27;: 0.41332716300321504}",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.season_midpoints",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "season_midpoints",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "{&#x27;Dec-Jan&#x27;: 1.0, &#x27;Feb-Mar&#x27;: 2.5, &#x27;Jun-Jul&#x27;: 6.5, &#x27;Aug-Sep&#x27;: 8.5, &#x27;Oct-Nov&#x27;: 10.5}",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.season_df",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "season_df",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "   month      coef\n1    1.0  0.737406\n2    2.5  0.285529\n3    6.5 -1.700071\n0    8.5 -1.486395\n4   10.5  0.413327",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.months_ext",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "months_ext",
      kind: "variable",
      doc: "<p></p>\n",
      default_value: "array([ 1. ,  2.5,  6.5,  8.5, 10.5, 13. ])",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.coef_ext",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "coef_ext",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "array([ 0.73740573,  0.28552867, -1.70007128, -1.48639529,  0.41332716,\n        0.73740573])",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.spl",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "spl",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "&lt;scipy.interpolate._fitpack2.UnivariateSpline object&gt;",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.months_full",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "months_full",
      kind: "variable",
      doc: "<p></p>\n",
      default_value: "array([ 1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12])",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.correction_factors",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "correction_factors",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "array([ 0.93332993,  0.25286965, -0.35949391, -0.87400028, -1.26088901,\n       -1.49039962, -1.53277167, -1.35824468, -0.94108979, -0.34830512,\n        0.26038429,  0.72122177])",
    },
    {
      fullname: "lactationcurve.WilminkCorrectionFactors.correction_df",
      modulename: "lactationcurve.WilminkCorrectionFactors",
      qualname: "correction_df",
      kind: "variable",
      doc: "<p></p>\n",
      default_value:
        "    Month  CorrectionFactor\n0       1          0.933330\n1       2          0.252870\n2       3         -0.359494\n3       4         -0.874000\n4       5         -1.260889\n5       6         -1.490400\n6       7         -1.532772\n7       8         -1.358245\n8       9         -0.941090\n9      10         -0.348305\n10     11          0.260384\n11     12          0.721222",
    },
  ];

  // mirrored in build-search-index.js (part 1)
  // Also split on html tags. this is a cheap heuristic, but good enough.
  elasticlunr.tokenizer.setSeperator(/[\s\-.;&_'"=,()]+|<[^>]*>/);

  let searchIndex;
  if (docs._isPrebuiltIndex) {
    console.info("using precompiled search index");
    searchIndex = elasticlunr.Index.load(docs);
  } else {
    console.time("building search index");
    // mirrored in build-search-index.js (part 2)
    searchIndex = elasticlunr(function () {
      this.pipeline.remove(elasticlunr.stemmer);
      this.pipeline.remove(elasticlunr.stopWordFilter);
      this.addField("qualname");
      this.addField("fullname");
      this.addField("annotation");
      this.addField("default_value");
      this.addField("signature");
      this.addField("bases");
      this.addField("doc");
      this.setRef("fullname");
    });
    for (let doc of docs) {
      searchIndex.addDoc(doc);
    }
    console.timeEnd("building search index");
  }

  return (term) =>
    searchIndex.search(term, {
      fields: {
        qualname: { boost: 4 },
        fullname: { boost: 2 },
        annotation: { boost: 2 },
        default_value: { boost: 2 },
        signature: { boost: 2 },
        bases: { boost: 2 },
        doc: { boost: 1 },
      },
      expand: true,
    });
})();
