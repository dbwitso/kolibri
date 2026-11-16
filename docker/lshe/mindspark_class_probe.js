// mindspark_class_probe.js
// Finds how a MindSpark learner is linked to their class/section (and whether
// accounts carry a role), without printing learner personal data. Read-only:
// it only calls find/findOne/distinct/countDocuments.
//
// Run on the MindSpark server from the normal shell:
//
//   mongosh "mongodb://<user>:<password>@127.0.0.1:27017/?authSource=admin" \
//     --quiet --file mindspark_class_probe.js > class_probe.txt
//
// Then send class_probe.txt to the Kolibri developer.
//
// Output:
//   1. the field paths of every UserManagement / UserAuthentication collection;
//   2. which collection + field references one sample learner's UID/UPID;
//   3. the distinct values of class/grade/section/role-like fields (labels only,
//      including nested fields such as products.Mindspark.grade).
//
// Section 2 scans every UserManagement collection once. On a large server run
// it outside teaching hours.

const um = db.getSiblingDB("UserManagement");
const ua = db.getSiblingDB("UserAuthentication");

// Label-like keys: class labels and roles are safe to print.
const LABEL_KEY = /(class|grade|section|batch|group|standard|level|division|role|type|category|product)/i;
// Keys like className / sectionName / groupLabel are class labels, not people's
// names, so they are checked before PII_KEY (which matches any "name").
const LABEL_NAME_KEY = /^(class|grade|section|batch|group|standard|division|level)_?(name|label|title|code)$/i;
// Anything that could identify a person is redacted.
const PII_KEY = /(name|dob|dateofbirth|birth|mobile|phone|email|address|parent|password|secret|token|username|pan)/i;

const MAX_DEPTH = 4;
const MAX_DISTINCT = 60;
const MAX_LABEL_LEN = 40;

function isBson(v) {
  // ObjectId, Long, Decimal128, Binary, etc. are leaves, not documents.
  return v !== null && typeof v === "object" && v._bsontype !== undefined;
}

function isLabelKey(key) {
  if (!key) return false;
  if (LABEL_NAME_KEY.test(key)) return true;
  return LABEL_KEY.test(key) && !PII_KEY.test(key);
}

function shape(v, key, depth) {
  if (depth > MAX_DEPTH) return "…";
  if (v === null || v === undefined) return "null";
  if (Array.isArray(v)) return v.length ? "[" + JSON.stringify(shape(v[0], key, depth + 1)) + "] (len " + v.length + ")" : "[]";
  if (v instanceof Date) return "date";
  if (isBson(v)) return "<" + v._bsontype + ">";
  if (typeof v === "object") {
    const out = {};
    Object.keys(v).forEach(k => { out[k] = shape(v[k], k, depth + 1); });
    return out;
  }
  if (typeof v === "string") {
    if (isLabelKey(key) && v.length <= MAX_LABEL_LEN) return "'" + v + "'";
    if (/^[0-9a-f]{24}$/.test(v)) return "<objectid-like>";
    return "<string>";
  }
  if (typeof v === "number" && isLabelKey(key)) return v;
  return typeof v;
}

// Which paths inside a doc hold `needle` (exact match, or inside an array)?
// Compares as strings so a UID stored as an ObjectId or number still matches.
function pathsContaining(doc, needle, prefix) {
  let hits = [];
  if (doc === null || doc === undefined) return hits;
  if (Array.isArray(doc)) {
    doc.forEach(x => { hits = hits.concat(pathsContaining(x, needle, prefix + "[]")); });
    return hits;
  }
  if (typeof doc === "object" && !isBson(doc) && !(doc instanceof Date)) {
    Object.keys(doc).forEach(k => {
      hits = hits.concat(pathsContaining(doc[k], needle, prefix ? prefix + "." + k : k));
    });
    return hits;
  }
  return String(doc) === String(needle) ? [prefix] : [];
}

// Dotted paths (no arrays) of label-like leaves in a document.
function labelPaths(doc, prefix, depth, out) {
  if (depth > MAX_DEPTH || doc === null || typeof doc !== "object" || isBson(doc) || doc instanceof Date) return out;
  if (Array.isArray(doc)) return out;
  Object.keys(doc).forEach(k => {
    const p = prefix ? prefix + "." + k : k;
    const v = doc[k];
    if (v !== null && typeof v === "object" && !isBson(v) && !(v instanceof Date) && !Array.isArray(v)) {
      labelPaths(v, p, depth + 1, out);
    } else if (isLabelKey(k)) {
      out.add(p);
    }
  });
  return out;
}

const DBS = [["UserManagement", um], ["UserAuthentication", ua]];

print("==== 1. Collection shapes (personal data redacted)");
DBS.forEach(([dbName, d]) => {
  d.getCollectionNames().sort().forEach(c => {
    const n = d.getCollection(c).countDocuments({});
    print("\n--- " + dbName + "." + c + "  (" + n + " docs)");
    printjson(shape(d.getCollection(c).findOne(), null, 0));
  });
});

// Sample: one ACTIVE learner (skip obvious staff/test accounts). Stops at the
// first match instead of looking up every active user.
const staff = /(coach|head|admin|test|teacher)/i;
let sample = null;
const cursor = um.UserDetails.find({ status: "A" });
while (!sample && cursor.hasNext()) {
  const u = cursor.next();
  const a = ua.Authentication.findOne({ UID: u.UID });
  if (a && a.username && !staff.test(a.username)) sample = u;
}
cursor.close();

print("\n==== 2. Where is a sample active learner referenced?");
if (!sample) {
  print("No active learner found.");
} else {
  const ids = { UID: sample.UID };
  if (sample.products && sample.products.Mindspark && sample.products.Mindspark.UPID) {
    ids.UPID = sample.products.Mindspark.UPID;
  }
  print("Sample keys being traced: " + Object.keys(ids).join(", "));
  print("UID stored as: " + (isBson(sample.UID) ? sample.UID._bsontype : typeof sample.UID));
  print("\nSample learner's own UserDetails (redacted):");
  printjson(shape(sample, null, 0));
  DBS.forEach(([dbName, d]) => {
    d.getCollectionNames().sort().forEach(c => {
      if (dbName === "UserManagement" && c === "UserDetails") return;
      let shown = 0;
      d.getCollection(c).find().forEach(doc => {
        Object.keys(ids).forEach(label => {
          const p = pathsContaining(doc, ids[label], "");
          if (p.length && shown < 3) {
            shown += 1;
            print("\n" + label + " found in " + dbName + "." + c + " at: " + p.join(", "));
            printjson(shape(doc, null, 0));
          }
        });
      });
    });
  });
}

print("\n==== 3. Distinct class-like and role-like values (labels only)");
DBS.forEach(([dbName, d]) => {
  d.getCollectionNames().sort().forEach(c => {
    const paths = new Set();
    // Look at a few documents, since optional fields may be missing in one.
    d.getCollection(c).find().limit(20).forEach(doc => labelPaths(doc, "", 0, paths));
    Array.from(paths).sort().forEach(p => {
      try {
        const vals = d.getCollection(c).distinct(p)
          .filter(v => (typeof v === "string" && v.length <= MAX_LABEL_LEN) || typeof v === "number");
        if (vals.length && vals.length <= MAX_DISTINCT) {
          print(dbName + "." + c + "." + p + ": " + JSON.stringify(vals));
        } else if (vals.length) {
          print(dbName + "." + c + "." + p + ": " + vals.length + " distinct values (too many to list)");
        }
      } catch (e) {
        print(dbName + "." + c + "." + p + ": distinct failed (" + e.message + ")");
      }
    });
  });
});

print("\n==== done");
