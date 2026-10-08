# AI Voice Receptionist
# +16062449157
Real-time voice agent for inbound calls: checks availability, books appointments via Cal.com, answers business FAQs from a knowledge base, and transfers to staff when needed.

## Build order
1. DB schema + seed business_knowledge/appointments
2. Core tools as plain, testable functions (Cal.com + pgvector calls, no realtime yet)
3. OpenAI Realtime session wiring, tested via a simple WebSocket client (no telephony yet)
4. Telephony webhook + audio bridge (Telnyx/Plivo)
5. Identity verification gate for existing-appointment actions
6. Staff dashboard

