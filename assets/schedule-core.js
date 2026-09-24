/**
 * Chopped Fantasy Football — offseason schedule core.
 *
 * Pure ESM with no dependencies and no DOM or Node APIs, so the same logic
 * powers the dashboard section (GitHub Pages) and the notifier that GitHub
 * Actions runs once a day.
 *
 * Unlike the ESPN side of the app, these dates are league decisions rather
 * than anything ESPN knows about, so they live in `data/offseason.json`.
 */

export const SCHEDULE_PATH = "data/offseason.json";

// How many days before an event a reminder goes out, unless the event
// overrides it with its own `remindersDaysBefore`.
export const DEFAULT_REMINDERS = [7, 1, 0];

const MS_PER_DAY = 86_400_000;
const ISO_DATE = /^(\d{4})-(\d{2})-(\d{2})$/;

/**
 * Days since the epoch for a `YYYY-MM-DD` string. Calendar dates are compared
 * as whole days, never as instants, so nothing shifts across a timezone.
 */
export function toDayNumber(isoDate) {
    const match = ISO_DATE.exec(String(isoDate ?? "").trim());

    if (!match) {
        return null;
    }

    const [, year, month, day] = match;

    return Math.round(
        Date.UTC(Number(year), Number(month) - 1, Number(day)) / MS_PER_DAY
    );
}

/**
 * Today's calendar date in the league's timezone. The notifier runs on a UTC
 * cron, so without this a 9pm ET event day would already be tomorrow.
 */
export function todayInZone(timeZone = "America/New_York", now = new Date()) {
    try {
        // en-CA formats as YYYY-MM-DD.
        return new Intl.DateTimeFormat("en-CA", {
            timeZone,
            year: "numeric",
            month: "2-digit",
            day: "2-digit"
        }).format(now);
    } catch {
        return now.toISOString().slice(0, 10);
    }
}

export function formatEventDate(isoDate, { weekday = true } = {}) {
    const dayNumber = toDayNumber(isoDate);

    if (dayNumber === null) {
        return String(isoDate ?? "");
    }

    return new Date(dayNumber * MS_PER_DAY).toLocaleDateString("en-US", {
        timeZone: "UTC",
        weekday: weekday ? "short" : undefined,
        month: "short",
        day: "numeric",
        year: "numeric"
    });
}

export function describeCountdown(daysUntil) {
    if (daysUntil === 0) {
        return "Today";
    }

    if (daysUntil === 1) {
        return "Tomorrow";
    }

    if (daysUntil === -1) {
        return "Yesterday";
    }

    return daysUntil > 0 ? `In ${daysUntil} days` : `${-daysUntil} days ago`;
}

function remindersFor(event) {
    const offsets = Array.isArray(event.remindersDaysBefore)
        ? event.remindersDaysBefore
        : DEFAULT_REMINDERS;

    return [...new Set(offsets.map(Number).filter((n) => Number.isInteger(n) && n >= 0))].sort(
        (a, b) => b - a
    );
}

/**
 * Resolve a raw schedule file against a given day: sort the events, work out
 * how far away each one is, and mark the next one still to come.
 *
 * Events with an unparseable or missing date are dropped rather than thrown
 * on, so one typo in the JSON can't blank out the whole section.
 */
export function buildSchedule(schedule, today) {
    const timezone = schedule?.timezone ?? "America/New_York";
    const reference = today ?? todayInZone(timezone);
    const todayNumber = toDayNumber(reference);

    const events = (schedule?.events ?? [])
        .map((event) => {
            const dayNumber = toDayNumber(event.date);

            if (dayNumber === null || todayNumber === null) {
                return null;
            }

            const daysUntil = dayNumber - todayNumber;

            return {
                ...event,
                id: event.id ?? event.date,
                dayNumber,
                daysUntil,
                status: daysUntil > 0 ? "UPCOMING" : daysUntil === 0 ? "TODAY" : "PAST",
                reminders: remindersFor(event)
            };
        })
        .filter(Boolean)
        .sort((a, b) => a.dayNumber - b.dayNumber);

    return {
        title: schedule?.title ?? "Offseason Schedule",
        timezone,
        today: reference,
        events,
        next: events.find((event) => event.daysUntil >= 0) ?? null
    };
}

/**
 * Every reminder that lands on `today` — an event fires once per offset in its
 * reminder list, so the same date can produce a 7-day warning one week and a
 * day-of alert the next.
 */
export function dueReminders(schedule, today) {
    const built = buildSchedule(schedule, today);

    return built.events
        .filter((event) => event.daysUntil >= 0 && event.reminders.includes(event.daysUntil))
        .map((event) => ({ event, daysBefore: event.daysUntil }));
}
