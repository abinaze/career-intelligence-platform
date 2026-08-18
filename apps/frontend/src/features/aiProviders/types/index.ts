/**
 * AI providers feature types.
 *
 * Currently covers exactly one provider (Anthropic, for chat) since
 * that's the only LLM integration that exists in this app — see
 * docs/desktop/TRANSFORMATION_PLAN.md section 7 for why local/other
 * hosted providers are intentionally deferred rather than speculated
 * on here.
 */

export interface TestConnectionResponse {
  success: boolean;
  message: string;
}
