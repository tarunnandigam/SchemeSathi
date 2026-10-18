// queries/mongodb_queries.js
// --------------------------
// Equivalent MongoDB shell queries for all four required pipelines.
// Run in MongoDB Compass Shell or mongosh.
// Use:  use scheme_reach

// ============================================================
// Pipeline 1: Most frequently missing documents
// ============================================================
db.applications.aggregate([
  { $match: { missing_documents: { $exists: true, $ne: [] } } },
  { $unwind: "$missing_documents" },
  {
    $group: {
      _id: "$missing_documents",
      count: { $sum: 1 }
    }
  },
  { $sort: { count: -1 } },
  {
    $project: {
      _id: 0,
      document_type: "$_id",
      count: 1
    }
  }
]);

// ============================================================
// Pipeline 2: Applications by status
// ============================================================
db.applications.aggregate([
  {
    $group: {
      _id: "$application_status",
      count: { $sum: 1 }
    }
  },
  { $sort: { count: -1 } },
  {
    $project: {
      _id: 0,
      status: "$_id",
      count: 1
    }
  }
]);

// ============================================================
// Pipeline 3: Incomplete applications by scheme
// ============================================================
db.applications.aggregate([
  { $match: { missing_documents: { $exists: true, $ne: [] } } },
  {
    $group: {
      _id: "$scheme_id",
      incomplete_count: { $sum: 1 }
    }
  },
  { $sort: { incomplete_count: -1 } },
  {
    $project: {
      _id: 0,
      scheme_id: "$_id",
      incomplete_count: 1
    }
  }
]);

// ============================================================
// Pipeline 4: Scheme names + incomplete counts ($lookup)
// ============================================================
db.applications.aggregate([
  { $match: { missing_documents: { $exists: true, $ne: [] } } },
  {
    $group: {
      _id: "$scheme_id",
      incomplete_count: { $sum: 1 }
    }
  },
  {
    $lookup: {
      from: "schemes",
      localField: "_id",
      foreignField: "scheme_id",
      as: "scheme_info"
    }
  },
  {
    $unwind: {
      path: "$scheme_info",
      preserveNullAndEmptyArrays: true
    }
  },
  {
    $project: {
      _id: 0,
      scheme_id: "$_id",
      scheme_name: { $ifNull: ["$scheme_info.name", "Unknown Scheme"] },
      category: { $ifNull: ["$scheme_info.category", "—"] },
      incomplete_count: 1
    }
  },
  { $sort: { incomplete_count: -1 } }
]);

// ============================================================
// Pipeline 5 (Optional): Stage duration analysis
// ============================================================
db.applications.aggregate([
  {
    $match: {
      application_status: { $in: ["approved", "rejected", "withdrawn"] },
      created_at: { $exists: true },
      updated_at: { $exists: true }
    }
  },
  {
    $project: {
      scheme_id: 1,
      application_status: 1,
      duration_days: {
        $divide: [
          { $subtract: ["$updated_at", "$created_at"] },
          1000 * 60 * 60 * 24
        ]
      }
    }
  },
  {
    $group: {
      _id: "$application_status",
      avg_days: { $avg: "$duration_days" },
      count: { $sum: 1 }
    }
  },
  {
    $project: {
      _id: 0,
      final_status: "$_id",
      avg_days_to_complete: { $round: ["$avg_days", 1] },
      record_count: "$count"
    }
  },
  { $sort: { avg_days_to_complete: 1 } }
]);

// ============================================================
// Basic CRUD queries for viva reference
// ============================================================

// Create: insert a scheme
db.schemes.insertOne({
  scheme_id: "SCH-TEST01",
  name: "Test Scheme",
  category: "Testing",
  department: "Test Dept",
  description: "Test description",
  benefits_description: "Test benefit",
  eligibility_criteria: ["Must be a test"],
  required_documents: ["identity_proof"],
  official_url: null,
  source_verified: false,
  active: true,
  created_at: new Date(),
  updated_at: new Date()
});

// Read: find all active schemes
db.schemes.find({ active: true }, { name: 1, category: 1, scheme_id: 1 }).sort({ name: 1 });

// Read: find application by ref
db.applications.findOne({ application_ref: "APP-000001" });

// Update: change scheme description
db.schemes.updateOne(
  { scheme_id: "SCH-TEST01" },
  { $set: { description: "Updated description", updated_at: new Date() } }
);

// Update: add a document and push stage history
db.applications.updateOne(
  { application_ref: "APP-000001" },
  {
    $addToSet: { documents_provided: "income_certificate" },
    $pull: { missing_documents: "income_certificate" },
    $push: {
      stage_history: {
        stage: "documents_pending",
        timestamp: new Date(),
        note: "Income certificate added"
      }
    },
    $set: { updated_at: new Date() }
  }
);

// Delete: remove test scheme (only safe when no references exist)
db.schemes.deleteOne({ scheme_id: "SCH-TEST01" });

// Check for referencing applications before deletion
db.applications.countDocuments({ scheme_id: "SCH-000001" });

// Validation: attempt invalid insert (will fail with validator active)
db.schemes.insertOne({
  name: "",
  category: "Bad",
  department: "Bad",
  active: true,
  created_at: new Date(),
  updated_at: new Date()
});
