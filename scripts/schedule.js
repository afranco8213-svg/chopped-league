#!/usr/bin/env node
/**
 * Prints the offseason schedule from data/offseason.json, the same file the
 * dashboard section and the email notifier read.
 */

import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

import {
    buildSchedule,
    describeCountdown,
    formatEventDate
} from "../assets/schedule-core.js";

export const SCHEDULE_FILE = fileURLToPath(
    new URL("../data/offseason.json", import.meta.url)
);

export async function readSchedule(file = SCHEDULE_FILE) {
    return JSON.parse(await readFile(file, "utf8"));
}

/** Only print when run directly, so notify.js can reuse readSchedule(). */
if (process.argv[1] === fileURLToPath(import.meta.url)) {
    const data = buildSchedule(await readSchedule());

    console.log();
    console.log("=".repeat(70));
    console.log(`CHOPPED — ${data.title.toUpperCase()}`);
    console.log(`TODAY: ${data.today} (${data.timezone})`);
    console.log("=".repeat(70));
    console.log();

    if (data.events.length === 0) {
        console.log("No key dates on the calendar yet.");
    }

    for (const event of data.events) {
        const marker =
            event.status === "TODAY" ? "🔴" : event.status === "PAST" ? "  " : "🟢";

        console.log(
            `${marker} ${formatEventDate(event.date).padEnd(20)} ` +
                `${event.name.padEnd(32)} ${describeCountdown(event.daysUntil)}`
        );

        if (event.description) {
            console.log(`      ${event.description}`);
        }
    }

    console.log();
    console.log("=".repeat(70));
    console.log(
        data.next
            ? `NEXT UP: ${data.next.name} — ${formatEventDate(data.next.date)} (${describeCountdown(data.next.daysUntil)})`
            : "Every key date has passed. Time for a new schedule."
    );
    console.log("=".repeat(70));
    console.log();
}
