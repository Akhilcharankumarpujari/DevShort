export interface Document {
  id: string
  name: string
  type: string
  client: string
  status: "pending" | "verified" | "failed"
  createdAt: string
  updatedAt: string
}

export interface Workflow {
  id: string
  name: string
  status: "active" | "inactive"
  stepsCount: number
  createdAt: string
}

export interface VerificationResult {
  documentId: string
  verified: boolean
  confidenceScore: number
  extractedFields: Record<string, any>
  matchedRules: string[]
  failures: string[]
}
