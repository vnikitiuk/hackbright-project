CREATE TABLE "transactions" (
  "transaction_id" serial PRIMARY KEY,
  "user_id" integer,
  "stock_symbol" text,
  "stock_count" numeric,
  "stock_price" numeric,
  "transaction_time" timestamp,
  "transaction_type" text
);

CREATE TABLE "users" (
  "user_id" serial PRIMARY KEY,
  "username" text,
  "password_hash" text,
  "cash_amount" numeric
);

ALTER TABLE "transactions" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("user_id");
