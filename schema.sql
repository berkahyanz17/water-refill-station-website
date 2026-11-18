create table stations (
  id text primary key,
  name text not null,
  campus text default '',
  status text default 'Layak Konsumsi',
  ph text default '',
  temperature text default '',
  last_test text default '',
  last_maintenance text default '',
  last_filter_change text default '',
  next_maintenance text default ''
);

create table reports (
  id bigint generated always as identity primary key,
  created_at timestamptz default now(),
  station text,
  type text,
  name text,
  message text
);

-- lock tables from public access; the app uses the service_role key server-side
alter table stations enable row level security;
alter table reports enable row level security;
