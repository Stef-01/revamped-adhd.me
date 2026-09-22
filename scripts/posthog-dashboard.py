#!/usr/bin/env python3
"""Build the ADHDme dashboard inside PostHog, from the same taxonomy analytics.js sends.

The site declares a closed set of events; this declares the tiles that read them back. Run it once
to create the dashboard, and again whenever the tiles below change — it matches existing insights
and cohorts by name and updates them in place, so it never leaves a second copy behind.

    export POSTHOG_PERSONAL_API_KEY=phx_...      # Settings -> Personal API keys, scope: read+write
    export POSTHOG_PROJECT_ID=12345              # optional; @current is resolved when omitted
    export POSTHOG_HOST=https://us.posthog.com   # or https://eu.posthog.com, or your own
    python3 scripts/posthog-dashboard.py

    python3 scripts/posthog-dashboard.py --dry-run     # print every payload, send nothing
    python3 scripts/posthog-dashboard.py --prune       # also delete tiles this file no longer names

Note the host: the personal API key talks to the app host (us.posthog.com), not the ingestion host
the browser posts events to (us.i.posthog.com). Either is accepted here; the ingestion form is
rewritten to the app form before the first request.

A tile built before its first event caches that empty result, and PostHog serves the cache
until something asks for a recompute. A newly built dashboard therefore reads zero against
data that is already there; opening it in the UI refreshes it, as does the refresh control
on any tile. It is not a sign the events are missing — check the Activity view before
assuming the site is at fault.

Nothing in the browser needs this key. It never goes near analytics-config.js.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

DASHBOARD = 'ADHDme — people and booking handoffs'
DASHBOARD_NOTE = (
    'Who is on the site, which clinician they went to book with, and which link took them there. '
    'Built by scripts/posthog-dashboard.py from the taxonomy in analytics.js; edit that script '
    'rather than the tiles, or the next run will put them back.'
)
WINDOW = '-30d'

# The categories analytics.js sends, in the words the site uses for them.
CATEGORIES = [('psychologist', 'Psychologists'), ('allied', 'Allied health'), ('gp', 'GPs'),
              ('exercise-physiology', 'Exercise physiology'), ('coach', 'Coaches')]


# --------------------------------------------------------------------------- query shorthand

# Breakdowns go in the `breakdowns` list. The older flat form — breakdown_type/breakdown —
# is still accepted by the API and still returns an empty result set, so a dashboard built
# with it looks configured and reads zero against data that is plainly there.
def events(*names, math='total'):
    return [{'kind': 'EventsNode', 'event': n, 'name': n, 'math': math} for n in names]


def trend(*names, math='total', breakdown=None, display='ActionsLineGraph', interval='day',
          properties=None, window=WINDOW):
    source = {
        'kind': 'TrendsQuery',
        'dateRange': {'date_from': window},
        'interval': interval,
        'series': events(*names, math=math),
        'trendsFilter': {'display': display},
        'filterTestAccounts': True,
    }
    if breakdown:
        source['breakdownFilter'] = {'breakdowns': [{'type': 'event', 'property': breakdown}], 'breakdown_limit': 25}
    if properties:
        source['properties'] = properties
    return {'kind': 'InsightVizNode', 'source': source}


def funnel(*names, breakdown=None, window=WINDOW):
    source = {
        'kind': 'FunnelsQuery',
        'dateRange': {'date_from': window},
        'series': [{'kind': 'EventsNode', 'event': n, 'name': n} for n in names],
        'funnelsFilter': {'funnelVizType': 'steps', 'funnelOrderType': 'ordered'},
        'filterTestAccounts': True,
    }
    if breakdown:
        source['breakdownFilter'] = {'breakdowns': [{'type': 'event', 'property': breakdown}], 'breakdown_limit': 25}
    return {'kind': 'InsightVizNode', 'source': source}


def sql(query):
    """A SQL tile. Trends answer "how many"; these answer the questions with a join or a ratio in
    them — which clinician converts the readers they get, which post produced a handoff, and what
    the network is asked for and has nobody for."""
    return {'kind': 'DataVisualizationNode',
            'source': {'kind': 'HogQLQuery', 'query': query},
            'display': 'ActionsTable'}


def lifecycle(event='$pageview', interval='week', window='-90d'):
    return {'kind': 'InsightVizNode', 'source': {
        'kind': 'LifecycleQuery',
        'dateRange': {'date_from': window},
        'interval': interval,
        'series': events(event),
        'filterTestAccounts': True,
    }}


def equals(key, value):
    return [{'key': key, 'value': [value], 'operator': 'exact', 'type': 'event'}]


# --------------------------------------------------------------------------- the tiles
# Order is the order they land on the dashboard. Each name is the key this script matches on, so
# renaming a tile here creates a new one; delete the old one in PostHog or run with --prune.

def tiles():
    out = [
        ('People on the site',
         'Distinct people per day. Click any point and PostHog lists the people behind it.',
         trend('$pageview', math='dau')),

        ('New and returning people',
         'Who is new, who came back, who has gone quiet. The people list opens from every band.',
         lifecycle()),

        ('People who clicked a booking link',
         'Distinct people, not clicks. This is the number that matters: one person hammering a '
         'button is still one person trying to book.',
         trend('booking-outbound', math='dau')),

        ('Booking clicks by clinician',
         'How many times each clinician’s booking link was followed.',
         trend('booking-outbound', breakdown='clinician_name', display='ActionsBarValue')),

        ('People who clicked, by clinician',
         'The same bars counted per person instead of per click.',
         trend('booking-outbound', math='dau', breakdown='clinician_name', display='ActionsBarValue')),

        ('Booking clicks by discipline',
         'Psychologist, allied health, GP, exercise physiology or coach. The site’s own five categories.',
         trend('booking-outbound', breakdown='category', display='ActionsBarValue')),

        ('Booking clicks by practice',
         'Which practice the handoff went to: GOALS Psychology, Wellness Psychology Clinic, REACH '
         'ADHD, Neurotherapy Clinics Australia, or a GP clinic.',
         trend('booking-outbound', breakdown='practice', display='ActionsBarValue')),

        ('Booking clicks by destination',
         'Healthengine, Halaxy, or a clinic’s own form. Where a click actually lands.',
         trend('booking-outbound', breakdown='destination', display='ActionsPie')),

        ('Which link they pressed',
         'Each named booking link on the site, counted separately.',
         trend('booking-outbound', breakdown='link', display='ActionsBarValue')),

        ('Which page they came from',
         'The surface the handoff started on: a profile page, or the network deck.',
         trend('booking-outbound', breakdown='surface', display='ActionsBarValue')),

        ('Profile views by clinician',
         'Who gets read. Pair it with the booking bars to see whose page is doing the work.',
         trend('profile-viewed', breakdown='clinician_name', display='ActionsBarValue')),

        ('Unique visitors by clinician',
         'Distinct people who opened each clinician’s page — the audience number, with one person '
         'reloading four times counted once. This is the fair comparison between two clinicians; '
         'the view count above is not.',
         trend('profile-viewed', math='dau', breakdown='clinician_name', display='ActionsBarValue')),

        ('Unique visitors by practice',
         'The same people count rolled up to the practice, so GOALS Psychology’s eight clinicians '
         'read as one audience rather than eight small ones.',
         trend('profile-viewed', math='dau', breakdown='practice', display='ActionsBarValue')),

        ('Unique visitors by clinician, by week',
         'Who is growing and who is going quiet. Weekly, and per person, so a single busy day '
         'does not read as a trend.',
         trend('profile-viewed', math='dau', breakdown='clinician_name',
               display='ActionsLineGraph', interval='week', window='-90d')),

        ('Diary bookings against enquiries',
         'The split that matters: a live diary (Healthengine, Halaxy) can end in an appointment '
         'there and then; a clinic contact form can only end in somebody being emailed back. '
         'Counting them together flatters whoever has a form.',
         trend('booking-outbound', breakdown='handoff_kind', display='ActionsBarValue')),

        ('Diary handoffs — people, by clinician',
         'Distinct people who went to a live diary, per clinician. The closest thing on this '
         'dashboard to "who is getting real bookings".',
         trend('booking-outbound', math='dau', breakdown='clinician_name',
               display='ActionsBarValue', properties=equals('handoff_kind', 'diary'))),

        ('How long they stayed on the practice’s page',
         'Booking links open in a new tab, so this site can time the tab next door. Under thirty '
         'seconds is a glance; minutes is a form being filled in. A handoff that never comes back '
         'raises nothing here at all, and that is the best outcome.',
         trend('booking-returned', breakdown='away_band', display='ActionsBarValue')),

        ('Cards opened on the network deck',
         'Which clinician card people press on The Network.',
         trend('deck-card-opened', breakdown='clinician_name', display='ActionsBarValue')),

        ('Landing → deck → profile → booking',
         'The whole funnel. The last step is a handoff, not a booking: whether an appointment '
         'happened is not observable from this site.',
         funnel('landing-viewed', 'deck-viewed', 'profile-viewed', 'booking-outbound')),

        ('Profile → booking, by clinician',
         'Of the people who open a clinician’s page, how many follow their booking link.',
         funnel('profile-viewed', 'booking-outbound', breakdown='clinician_name')),

        ('Which door they came through',
         'The named controls on the landing page and in the header.',
         trend('landing-cta', breakdown='control', display='ActionsBarValue')),

        ('Pages opened',
         'Every page of the site, in the site’s own words.',
         trend('page-viewed', breakdown='page', display='ActionsBarValue')),
    ]
    out += [
        ('Clinician scorecard (30 days)',
         'One row per clinician: how many people saw their card, opened their page, and went on to '
         'book. The rate counts people, not clicks, so it cannot exceed 100%. days_since is blank '
         'for anyone who has never had a handoff.',
         sql("""
select properties.clinician_name                                        as clinician,
       anyIf(properties.practice, event = 'profile-viewed')             as practice,
       anyIf(properties.category, event = 'profile-viewed')             as discipline,
       uniqIf(person_id, event = 'deck-card-opened')                    as saw_card,
       uniqIf(person_id, event = 'profile-viewed')                      as read_page,
       uniqIf(person_id, event = 'booking-outbound')                    as booked,
       round(100.0 * uniqIf(person_id, event = 'booking-outbound')
             / nullIf(uniqIf(person_id, event = 'profile-viewed'), 0), 1) as pct_of_readers,
       countIf(event = 'booking-outbound')                              as handoff_clicks,
       if(countIf(event = 'booking-outbound') = 0, null,
          dateDiff('day', maxIf(timestamp, event = 'booking-outbound'), now())) as days_since
from events
where properties.$host in ('www.adhdme.au', 'adhdme.au')
  and timestamp > now() - interval 30 day
  and event in ('deck-card-opened', 'profile-viewed', 'booking-outbound')
  and properties.clinician_name is not null
group by clinician
order by booked desc, read_page desc""")),

        ('Provider leaderboard — clicks against likely bookings (30 days)',
         'The ranking table. unique_visitors is people, not page views. diary_people reached a '
         'live diary where an appointment can be made; enquiry_people could only send a message. '
         'likely_booked is a proxy, not a count: a diary handoff they did not bounce back from '
         'within two minutes. The only ground truth is the practice’s own diary.',
         sql("""
select properties.clinician_name                                      as clinician,
       anyIf(properties.practice, event = 'profile-viewed')           as practice,
       anyIf(properties.category, event = 'profile-viewed')           as discipline,
       uniqIf(person_id, event = 'profile-viewed')                    as unique_visitors,
       countIf(event = 'booking-outbound')                            as handoff_clicks,
       uniqIf(person_id, event = 'booking-outbound')                  as handoff_people,
       uniqIf(person_id, event = 'booking-outbound'
              and properties.handoff_kind = 'diary')                  as diary_people,
       uniqIf(person_id, event = 'booking-outbound'
              and properties.handoff_kind = 'enquiry')                as enquiry_people,
       greatest(0, countIf(event = 'booking-outbound'
                           and properties.handoff_kind = 'diary')
                 - countIf(event = 'booking-returned'
                           and properties.handoff_kind = 'diary'
                           and properties.away_band in ('under-30s', '30s-2m')))
                                                                      as likely_booked,
       countIf(event = 'booking-returned'
               and properties.away_band = 'under-30s')                as bounced_straight_back,
       round(100.0 * uniqIf(person_id, event = 'booking-outbound')
             / nullIf(uniqIf(person_id, event = 'profile-viewed'), 0), 1) as pct_of_visitors
from events
where properties.$host in ('www.adhdme.au', 'adhdme.au')
  and timestamp > now() - interval 30 day
  and event in ('profile-viewed', 'booking-outbound', 'booking-returned')
  and properties.clinician_name is not null
group by clinician
order by likely_booked desc, diary_people desc, unique_visitors desc""")),

        ('Practice leaderboard (30 days)',
         'The same table one level up. A practice with eight clinicians should be compared with '
         'other practices, not with one solo coach.',
         sql("""
select properties.practice                                            as practice,
       uniq(properties.clinician_name)                                as clinicians_seen,
       uniqIf(person_id, event = 'profile-viewed')                    as unique_visitors,
       uniqIf(person_id, event = 'booking-outbound')                  as handoff_people,
       uniqIf(person_id, event = 'booking-outbound'
              and properties.handoff_kind = 'diary')                  as diary_people,
       greatest(0, countIf(event = 'booking-outbound'
                           and properties.handoff_kind = 'diary')
                 - countIf(event = 'booking-returned'
                           and properties.handoff_kind = 'diary'
                           and properties.away_band in ('under-30s', '30s-2m')))
                                                                      as likely_booked,
       round(100.0 * uniqIf(person_id, event = 'booking-outbound')
             / nullIf(uniqIf(person_id, event = 'profile-viewed'), 0), 1) as pct_of_visitors
from events
where properties.$host in ('www.adhdme.au', 'adhdme.au')
  and timestamp > now() - interval 30 day
  and event in ('profile-viewed', 'booking-outbound', 'booking-returned')
  and properties.practice is not null
group by practice
order by likely_booked desc, unique_visitors desc""")),

        ('Clicks that did not hold (30 days)',
         'The other side of the leaderboard: handoffs where they were back on this site within two '
         'minutes. A high rate here against a healthy click count means the booking page itself is '
         'losing them — a full diary, a surprise fee, a login wall — not this site.',
         sql("""
select properties.clinician_name                              as clinician,
       any(properties.destination)                            as lands_on,
       count()                                                as returns,
       countIf(properties.away_band = 'under-30s')            as under_30s,
       countIf(properties.away_band = '30s-2m')               as half_to_two_min,
       countIf(properties.away_band in ('2m-10m', 'over-10m')) as long_enough_to_book,
       round(avg(toFloat(properties.away)), 0)                as avg_seconds_away
from events
where properties.$host in ('www.adhdme.au', 'adhdme.au')
  and timestamp > now() - interval 30 day
  and event = 'booking-returned'
group by clinician
order by under_30s desc""")),

        ('Share of the network’s attention (30 days)',
         'What proportion of everybody who read any clinician page read this one. Says whether '
         'the network is spreading demand or funnelling it all at two people.',
         sql("""
select properties.clinician_name   as clinician,
       any(properties.practice)    as practice,
       uniq(person_id)             as unique_visitors,
       round(100.0 * uniq(person_id)
             / nullIf((select uniq(person_id) from events
                       where properties.$host in ('www.adhdme.au', 'adhdme.au')
  and timestamp > now() - interval 30 day
                         and event = 'profile-viewed'), 0), 1) as pct_of_all_readers
from events
where properties.$host in ('www.adhdme.au', 'adhdme.au')
  and timestamp > now() - interval 30 day
  and event = 'profile-viewed'
  and properties.clinician_name is not null
group by clinician
order by unique_visitors desc""")),

        ('New against returning visitors, by clinician (30 days)',
         'Whether a clinician’s audience is new arrivals or the same people coming back to decide. '
         'Somebody on their third read of one profile is close to acting and has not yet.',
         sql("""
select properties.clinician_name                          as clinician,
       uniq(person_id)                                    as people,
       count()                                            as views,
       round(count() / nullIf(uniq(person_id), 0), 2)     as views_per_person,
       countIf(event = 'booking-outbound')                as handoffs
from events
where properties.$host in ('www.adhdme.au', 'adhdme.au')
  and timestamp > now() - interval 30 day
  and event in ('profile-viewed', 'booking-outbound')
  and properties.clinician_name is not null
group by clinician
order by views_per_person desc""")),

        ('Starved of referrals',
         'Listed, read, and not booked once in 30 days. Supply health: a clinician nobody is sent '
         'to is the network failing them, and that never shows up in a total.',
         sql("""
select properties.clinician_name    as clinician,
       any(properties.practice)     as practice,
       any(properties.category)     as discipline,
       uniq(person_id)              as readers,
       max(timestamp)               as last_read
from events
where properties.$host in ('www.adhdme.au', 'adhdme.au')
  and timestamp > now() - interval 30 day
  and event = 'profile-viewed'
  and properties.clinician_name is not null
  and properties.clinician_name not in (
        select properties.clinician_name from events
        where properties.$host in ('www.adhdme.au', 'adhdme.au')
  and timestamp > now() - interval 30 day and event = 'booking-outbound')
group by clinician
order by readers desc""")),

        ('What the network is asked for',
         'Demand by expertise, per person. A profile view counts towards every expertise that '
         'clinician carries, so this reads what people came looking for rather than who they '
         'happened to land on. A wide gap between read and booked is where supply is thin.',
         sql("""
select arrayJoin(JSONExtract(ifNull(properties.expertise, '[]'), 'Array(String)')) as expertise,
       uniqIf(person_id, event = 'profile-viewed')      as read_someone,
       uniqIf(person_id, event = 'booking-outbound')    as booked_someone,
       round(100.0 * uniqIf(person_id, event = 'booking-outbound')
             / nullIf(uniqIf(person_id, event = 'profile-viewed'), 0), 1) as pct
from events
where properties.$host in ('www.adhdme.au', 'adhdme.au')
  and timestamp > now() - interval 30 day
  and event in ('profile-viewed', 'booking-outbound')
  and properties.expertise is not null
group by expertise
order by read_someone desc""")),

        ('Read the fees and did not book',
         'The cohort worth reading: got as far as the fee table on a clinician page and left '
         'without following the booking link. Fills from the day profile-engaged ships.',
         sql("""
select properties.clinician_name                                  as clinician,
       any(properties.practice)                                   as practice,
       countIf(properties.acted = 'no'
               and properties.depth in ('fees','network','end'))  as read_and_left,
       countIf(properties.acted = 'yes')                          as read_and_booked,
       round(avgIf(toFloat(properties.dwell), properties.acted = 'no'), 0) as avg_seconds_before_leaving
from events
where properties.$host in ('www.adhdme.au', 'adhdme.au')
  and timestamp > now() - interval 30 day
  and event = 'profile-engaged'
group by clinician
order by read_and_left desc""")),

        ('How far profiles are read',
         'Where attention stops: the hero, the fee table, the rest of the network, or the foot of '
         'the page. A page nobody scrolls is a different problem from one they read and leave.',
         trend('profile-engaged', breakdown='depth', display='ActionsBarValue')),

        ('Which post produced the handoff',
         'Every tagged post that led to a booking link being followed. Tag links as '
         '?utm_source=<channel>&utm_campaign=<theme>&utm_content=<post>.',
         sql("""
select properties.content_post                          as post,
       any(properties.content_theme)                    as theme,
       any(properties.channel)                          as channel,
       uniqIf(person_id, event = 'page-viewed')         as arrived,
       uniqIf(person_id, event = 'booking-outbound')    as booked,
       round(100.0 * uniqIf(person_id, event = 'booking-outbound')
             / nullIf(uniqIf(person_id, event = 'page-viewed'), 0), 1) as pct
from events
where properties.$host in ('www.adhdme.au', 'adhdme.au')
  and timestamp > now() - interval 90 day
  and event in ('page-viewed', 'booking-outbound')
  and properties.content_post is not null
  and properties.content_post != 'none'
group by post
order by booked desc, arrived desc""")),

        ('Content theme against bookings, by week',
         'The cross-compare: what was posted about, and whether handoffs followed. One row per '
         'theme per week, so a spike lines up against the content calendar.',
         sql("""
select toStartOfWeek(timestamp)                     as week,
       ifNull(properties.content_theme, 'untagged') as theme,
       uniqIf(person_id, event = 'page-viewed')     as arrived,
       countIf(event = 'booking-outbound')          as handoffs
from events
where properties.$host in ('www.adhdme.au', 'adhdme.au')
  and timestamp > now() - interval 90 day
  and event in ('page-viewed', 'booking-outbound')
group by week, theme
order by week desc, handoffs desc""")),

        ('Handoffs by week, by clinician',
         'Who is trending. Week over week rather than a running total, so a clinician going quiet '
         'shows up instead of being carried by their history.',
         trend('booking-outbound', breakdown='clinician_name', display='ActionsLineGraph',
               interval='week', window='-90d')),

        ('Where visits come from',
         'Channel for every visit, tagged or inferred from the referrer.',
         trend('page-viewed', breakdown='channel', display='ActionsPie')),
    ]
    for key, label in CATEGORIES:
        out.append((
            f'Booking clicks — {label}',
            f'Just the {label.lower()}, broken out by clinician.',
            trend('booking-outbound', breakdown='clinician_name', display='ActionsBarValue',
                  properties=equals('category', key)),
        ))
    return out


# --------------------------------------------------------------------------- the people lists
# A cohort is a list of actual people you can open, scroll and export — the answer to "show me
# everybody who tried to book with a psychologist".

def behavioural(event, days=90, properties=None):
    node = {
        'key': event, 'type': 'behavioral', 'value': 'performed_event', 'event_type': 'events',
        'time_value': days, 'time_interval': 'day', 'operator': 'gte', 'operator_value': 1,
    }
    if properties:
        node['event_filters'] = properties
    return {'properties': {'type': 'OR', 'values': [{'type': 'AND', 'values': [node]}]}}


def cohorts():
    out = [
        ('Clicked a booking link (90 days)',
         'Everybody who followed any clinician’s booking link in the last 90 days.',
         behavioural('booking-outbound')),
        ('Read a profile but did not book (90 days)',
         'Opened a clinician’s page and never followed a booking link. The gap worth reading.',
         {'properties': {'type': 'AND', 'values': [
             {'type': 'AND', 'values': [{
                 'key': 'profile-viewed', 'type': 'behavioral', 'value': 'performed_event',
                 'event_type': 'events', 'time_value': 90, 'time_interval': 'day',
             }]},
             {'type': 'AND', 'values': [{
                 'key': 'booking-outbound', 'type': 'behavioral', 'value': 'performed_event',
                 'event_type': 'events', 'time_value': 90, 'time_interval': 'day',
                 'negation': True,
             }]},
         ]}}),
    ]
    out += [
        ('Went to a live diary (90 days)',
         'Everybody who followed a link to Healthengine or Halaxy, where an appointment can '
         'actually be made — as opposed to a clinic contact form.',
         behavioural('booking-outbound', properties=equals('handoff_kind', 'diary'))),

        ('Likely booked — diary, no quick return (90 days)',
         'Went to a live diary and did not come straight back to this site. The nearest thing to '
         'a list of people who booked. A proxy: somebody who closed the tab entirely looks the '
         'same as somebody who completed a form.',
         {'properties': {'type': 'AND', 'values': [
             {'type': 'AND', 'values': [{
                 'key': 'booking-outbound', 'type': 'behavioral', 'value': 'performed_event',
                 'event_type': 'events', 'time_value': 90, 'time_interval': 'day',
                 'event_filters': equals('handoff_kind', 'diary'),
             }]},
             {'type': 'AND', 'values': [{
                 'key': 'booking-returned', 'type': 'behavioral', 'value': 'performed_event',
                 'event_type': 'events', 'time_value': 90, 'time_interval': 'day',
                 'event_filters': [{'key': 'away_band', 'value': ['under-30s', '30s-2m'],
                                    'operator': 'exact', 'type': 'event'}],
                 'negation': True,
             }]},
         ]}}),

        ('Bounced off the booking page (90 days)',
         'Followed a booking link and was back here within thirty seconds. Something on the '
         'practice’s page turned them around, and it is worth knowing what.',
         behavioural('booking-returned',
                     properties=[{'key': 'away_band', 'value': ['under-30s'],
                                  'operator': 'exact', 'type': 'event'}])),

        ('Still shopping — three or more clinicians tried (90 days)',
         'Followed booking links for three or more different clinicians. Not a happy customer: '
         'somebody who cannot get in anywhere.',
         {'properties': {'type': 'AND', 'values': [{'type': 'AND', 'values': [
             {'key': 'adhdme_clinicians_tried', 'type': 'person', 'value': '3', 'operator': 'gte'},
         ]}]}}),
    ]
    for key, label in CATEGORIES:
        out.append((
            f'Clicked a booking link — {label} (90 days)',
            f'Everybody who went to book with one of the {label.lower()}.',
            behavioural('booking-outbound', properties=equals('category', key)),
        ))
    return out


# --------------------------------------------------------------------------- the replay lists
# Replay is only worth having if you never have to scroll a thousand recordings to find the one
# that matters. Each playlist below is a standing question; PostHog fills it as recordings arrive.

def replay_filter(event, days=30, properties=None):
    node = {'id': event, 'name': event, 'type': 'events', 'order': 0}
    if properties:
        node['properties'] = properties
    return {'events': [node], 'date_from': f'-{days}d', 'filter_test_accounts': True}


def playlists():
    return [
        ('Watch: they went to book',
         'Every recording that ends in a booking link being followed. Watch these first — this is '
         'what the site working looks like.',
         replay_filter('booking-outbound')),
        ('Watch: bounced off the booking page',
         'They followed a booking link and were back within thirty seconds. The most useful '
         'thirty seconds of video on this dashboard: whatever turned them around is on screen.',
         replay_filter('booking-returned',
                       properties=[{'key': 'away_band', 'value': ['under-30s'],
                                    'operator': 'exact', 'type': 'event'}])),
        ('Watch: read the fees and left',
         'Got as far down a clinician’s page as the fee table and never pressed anything. Where '
         'the cost conversation is actually being lost.',
         replay_filter('profile-engaged',
                       properties=[{'key': 'acted', 'value': ['no'], 'operator': 'exact',
                                    'type': 'event'},
                                   {'key': 'depth', 'value': ['fees', 'network', 'end'],
                                    'operator': 'exact', 'type': 'event'}])),
    ]


# --------------------------------------------------------------------------- the API

class PostHog:
    def __init__(self, host, token, project, dry_run=False):
        self.host = host.rstrip('/')
        self.token = token
        self.project = project
        self.dry_run = dry_run

    def request(self, method, path, body=None):
        url = f'{self.host}{path}'
        if self.dry_run and method in ('POST', 'PATCH', 'DELETE'):
            print(f'  would {method} {path}')
            if body is not None:
                print('    ' + json.dumps(body, ensure_ascii=False)[:2000])
            return {'id': 0, 'name': (body or {}).get('name', ''), 'results': []}
        if self.dry_run and not self.token:
            # Offline preview: read nothing, so every tile reads as new.
            return {'id': 0, 'results': [], 'next': None}
        data = json.dumps(body).encode('utf-8') if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
        })
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read().decode('utf-8')
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            detail = e.read().decode('utf-8', 'replace')[:1000]
            raise SystemExit(f'posthog-dashboard: {method} {path} failed with {e.code}\n  {detail}')
        except urllib.error.URLError as e:
            raise SystemExit(f'posthog-dashboard: cannot reach {self.host} ({e.reason})')

    def api(self, path):
        return f'/api/projects/{self.project}{path}'

    def collect(self, path, limit=500):
        """Every page of a paginated list endpoint."""
        rows, url = [], f'{path}?limit=100'
        while url and len(rows) < limit:
            page = self.request('GET', url)
            rows.extend(page.get('results', []))
            nxt = page.get('next')
            if not nxt:
                break
            url = nxt[len(self.host):] if nxt.startswith(self.host) else nxt
        return rows


def resolve_project(client):
    if client.project:
        return client.project
    client.project = '@current'
    me = client.request('GET', '/api/projects/@current/')
    pid = me.get('id')
    if not pid:
        raise SystemExit('posthog-dashboard: could not resolve the current project; set POSTHOG_PROJECT_ID')
    return pid


def app_host(host):
    """The personal API key talks to the app host, not the ingestion host."""
    return (host.replace('//us.i.posthog.com', '//us.posthog.com')
                .replace('//eu.i.posthog.com', '//eu.posthog.com')
                .replace('//us-assets.i.posthog.com', '//us.posthog.com')
                .replace('//eu-assets.i.posthog.com', '//eu.posthog.com'))


# --------------------------------------------------------------------------- the run

# PostHog caps a description at 400 characters and rejects the whole object with a 400 when it is
# longer. Found the hard way, twenty tiles into a run: the dashboard was left half built. Check
# every payload before the first request instead.
DESCRIPTION_LIMIT = 400


def audit():
    over = [(kind, name, len(note))
            for kind, items in (('tile', tiles()), ('cohort', cohorts()), ('playlist', playlists()))
            for name, note, _ in items if len(note) > DESCRIPTION_LIMIT]
    if over:
        lines = '\n'.join(f'  {k} "{n}" — {c} characters' for k, n, c in over)
        raise SystemExit(f'posthog-dashboard: {len(over)} description(s) over the '
                         f'{DESCRIPTION_LIMIT}-character limit PostHog enforces:\n{lines}')
    names = [n for _, items in (('t', tiles()), ('c', cohorts()), ('p', playlists()))
             for n, _, _ in items]
    dupes = sorted({n for n in names if names.count(n) > 1})
    if dupes:
        raise SystemExit('posthog-dashboard: two objects share a name, so each run would '
                         'overwrite the other: ' + ', '.join(dupes))


def sync(client, prune=False):
    dashboards = client.collect(client.api('/dashboards/'))
    existing = next((d for d in dashboards if d.get('name') == DASHBOARD), None)
    if existing:
        board = client.request('PATCH', client.api(f'/dashboards/{existing["id"]}/'),
                               {'description': DASHBOARD_NOTE, 'pinned': True})
        board_id = existing['id']
        print(f'dashboard: reusing "{DASHBOARD}" (#{board_id})')
    else:
        board = client.request('POST', client.api('/dashboards/'),
                               {'name': DASHBOARD, 'description': DASHBOARD_NOTE, 'pinned': True})
        board_id = board.get('id')
        print(f'dashboard: created "{DASHBOARD}" (#{board_id})')

    insights = {i.get('name'): i for i in client.collect(client.api('/insights/')) if i.get('name')}
    wanted = tiles()
    for name, note, query in wanted:
        payload = {'name': name, 'description': note, 'query': query, 'dashboards': [board_id]}
        found = insights.get(name)
        if found:
            client.request('PATCH', client.api(f'/insights/{found["id"]}/'), payload)
            print(f'  tile  · updated  {name}')
        else:
            client.request('POST', client.api('/insights/'), payload)
            print(f'  tile  · created  {name}')

    if prune:
        keep = {name for name, _, _ in wanted}
        for name, found in insights.items():
            on_board = board_id in [d if isinstance(d, int) else d.get('id') for d in (found.get('dashboards') or [])]
            if on_board and name not in keep:
                client.request('PATCH', client.api(f'/insights/{found["id"]}/'), {'dashboards': []})
                print(f'  tile  · removed  {name}')

    have = {c.get('name'): c for c in client.collect(client.api('/cohorts/')) if c.get('name')}
    for name, note, filters in cohorts():
        payload = {'name': name, 'description': note, 'filters': filters, 'is_static': False}
        found = have.get(name)
        if found:
            client.request('PATCH', client.api(f'/cohorts/{found["id"]}/'), payload)
            print(f'  people · updated  {name}')
        else:
            client.request('POST', client.api('/cohorts/'), payload)
            print(f'  people · created  {name}')

    # Replay playlists. Matched by name like everything else, so a re-run updates rather than
    # duplicates. The endpoint is newer than the rest of the API and not on every plan; a failure
    # here should not lose the dashboard that already built, so it is reported and stepped over.
    try:
        have = {p.get('name'): p for p in client.collect(client.api('/session_recording_playlists/'))
                if p.get('name')}
    except SystemExit as e:
        print(f'  replay · skipped ({e})')
        return board_id
    for name, note, filters in playlists():
        # `type` is required and is not inferred from the payload: without it the endpoint answers
        # 400 "Must provide a valid playlist type". 'filters' is a standing query, as against a
        # 'collection', which is a hand-picked list of recordings.
        payload = {'name': name, 'description': note, 'type': 'filters',
                   'filters': filters, 'pinned': True}
        found = have.get(name)
        try:
            if found:
                client.request('PATCH', client.api(f'/session_recording_playlists/{found["short_id"]}/'), payload)
                print(f'  replay · updated  {name}')
            else:
                client.request('POST', client.api('/session_recording_playlists/'), payload)
                print(f'  replay · created  {name}')
        except SystemExit as e:
            print(f'  replay · failed   {name} ({e})')

    return board_id


def main(argv):
    ap = argparse.ArgumentParser(description='Create or refresh the ADHDme dashboard in PostHog.')
    ap.add_argument('--dry-run', action='store_true', help='print every payload and send nothing')
    ap.add_argument('--prune', action='store_true', help='take tiles this file no longer names off the dashboard')
    ap.add_argument('--host', default=os.environ.get('POSTHOG_HOST', 'https://us.posthog.com'))
    ap.add_argument('--project', default=os.environ.get('POSTHOG_PROJECT_ID', ''))
    args = ap.parse_args(argv)

    token = os.environ.get('POSTHOG_PERSONAL_API_KEY', '')
    if not token and not args.dry_run:
        print('posthog-dashboard: set POSTHOG_PERSONAL_API_KEY (Settings -> Personal API keys), '
              'or pass --dry-run to see what would be sent.', file=sys.stderr)
        return 2

    audit()
    host = app_host(args.host)
    client = PostHog(host, token, args.project, dry_run=args.dry_run)
    if args.dry_run and not args.project:
        client.project = 'PROJECT_ID'
    else:
        client.project = resolve_project(client)

    print(f'posthog-dashboard: {host}, project {client.project}'
          + (' (dry run)' if args.dry_run else ''))
    board_id = sync(client, prune=args.prune)

    if not args.dry_run:
        print()
        print(f'  dashboard  {host}/project/{client.project}/dashboard/{board_id}')
        print(f'  people     {host}/project/{client.project}/persons')
        print(f'  cohorts    {host}/project/{client.project}/cohorts')
        print()
        print('Every bar and every point opens the list of people behind it: click a data point, '
              'then "View persons".')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
