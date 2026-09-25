-- Idempotency constraints for payment and ledger records.
-- Run after checking/removing any duplicate historical rows.

ALTER TABLE order_pay
    ADD UNIQUE KEY uniq_order_pay_order_id (order_id),
    ADD UNIQUE KEY uniq_order_pay_transaction_id (transaction_id);

ALTER TABLE order_m_list
    ADD UNIQUE KEY uniq_order_m_order_id (order_id);

ALTER TABLE order_u_list
    ADD UNIQUE KEY uniq_order_u_order_id (order_id);
