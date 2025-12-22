/**
 * API Types - Mirrors backend Pydantic schemas
 * @module api/types
 */

/**
 * @typedef {Object} User
 * @property {string} id - UUID
 * @property {string} email
 * @property {string} created_at - ISO timestamp
 */

/**
 * @typedef {Object} UserCreate
 * @property {string} email
 * @property {string} password
 */

/**
 * @typedef {Object} Token
 * @property {string} access_token
 * @property {string} token_type
 */

/**
 * @typedef {Object} LoginRequest
 * @property {string} email
 * @property {string} password
 */

/**
 * @typedef {Object} RegisterRequest
 * @property {string} email
 * @property {string} password
 */

/**
 * @typedef {'pending' | 'processing' | 'processed' | 'failed'} EntryStatus
 */

/**
 * @typedef {Object} JournalEntry
 * @property {string} id - UUID
 * @property {string} user_id - UUID
 * @property {string} audio_url
 * @property {string|null} transcript
 * @property {string|null} summary
 * @property {string|null} emotion
 * @property {EntryStatus} status
 * @property {string} created_at - ISO timestamp
 * @property {string} updated_at - ISO timestamp
 */

/**
 * @typedef {Object} EntryCreateResponse
 * @property {string} id
 * @property {string} audio_url
 * @property {string} message
 */

/**
 * @typedef {Object} EntryListResponse
 * @property {JournalEntry[]} entries
 * @property {number} total
 * @property {number} skip
 * @property {number} limit
 */

/**
 * @typedef {Object} ApiError
 * @property {string} detail
 */

export const EntryStatus = {
    PENDING: 'pending',
    PROCESSING: 'processing',
    PROCESSED: 'processed',
    FAILED: 'failed'
};
