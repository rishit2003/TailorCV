// MongoDB Initialization Script for TailorCV
// This script will run when MongoDB container first starts
// It creates the database, collections, and indexes
//
// Purpose:
// - Create tailorcv_db database
// - Create cvs collection
// - Set up indexes for query performance
// - Optional: Insert sample/seed data for testing
//
// TODO: Implement the following when setting up MongoDB:
//
// 1. Switch to tailorcv_db database:
//    db = db.getSiblingDB('tailorcv_db');
//
// 2. Create collections:
//    db.createCollection('cvs');
//
// 3. Create indexes:
//    a. Unique index on cv_id (hash-based identifier):
//       db.cvs.createIndex({ cv_id: 1 }, { unique: true, name: 'cv_id_unique_idx' });
//
//    b. Index on created_at for sorting (getLatestCV queries):
//       db.cvs.createIndex({ created_at: -1 }, { name: 'created_at_desc_idx' });
//
//    c. Optional compound index if adding user_id later:
//       db.cvs.createIndex({ user_id: 1, created_at: -1 }, { name: 'user_latest_cv_idx' });
//
// 4. Optional: Insert sample document for testing:
//    db.cvs.insertOne({
//      cv_id: 'sample_hash_12345',
//      cv_text: 'Sample CV text...',
//      structured_json: { experience: [], projects: [], skills: [], education: [] },
//      created_at: new Date(),
//      updated_at: new Date()
//    });
//
// Usage with docker-compose:
// Mount this file in docker-compose.yml:
//
// services:
//   mongodb:
//     image: mongo:latest
//     volumes:
//       - ./configs/mongodb-init.js:/docker-entrypoint-initdb.d/init.js:ro
//
// Document Schema Reference:
// {
//   "_id": ObjectId,              // MongoDB auto-generated
//   "cv_id": "sha256_hash",       // Our primary identifier (hash of CV text)
//   "cv_text": "original text",   // Raw CV text
//   "structured_json": {...},     // Sections: experience, projects, skills, education
//   "created_at": ISODate,
//   "updated_at": ISODate
// }

