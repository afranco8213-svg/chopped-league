#!/usr/bin/env node
/**
 * Emails the league about offseason key dates. GitHub Actions runs this once
 * a day; anything in data/offseason.json whose reminder offsets land on today
 * goes out as a single digest.
 *
 * Config comes from the environment so no addresses or credentials live in
 * this public repo:
 *
 *   GMAIL_USER           the Gmail address that sends
 *   GMAIL_APP_PASSWORD   a Google app password (not the account password)
 *   NOTIFY_TO            comma-separated recipients
 *   NOTIFY_FROM_NAME     optional sender name (default "Chopped League")
 *   SITE_URL             optional dashboard link included in the email
 *
 * Flags:
 *   --dry-run            print the email instead of sending it
 *   --date=YYYY-MM-DD    pretend today is this date
 */

import {
    buildSchedule,
    describeCountdown,
    dueReminders,
    formatEventDate,
    todayInZone
} from "../assets/schedule-core.js";

import { readSchedule } from "./schedule.js";

const args = process.argv.slice(2);
const dryRun = args.includes("--dry-run");
const dateArg = args.find((arg) => arg.startsWith("--date="))?.slice("--date=".length);

function escapeHtml(value) {
    return String(value).replace(
        /[&<>"']/g,
        (character) =>
            ({
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#39;"
            })[character]
    );
}

function headline(daysBefore, event) {
    if (daysBefore === 0) {
        return `TODAY — ${event.name}`;
    }

    return `${daysBefore} day${daysBefore === 1 ? "" : "s"} out — ${event.name}`;
}

function buildSubject(due) {
    if (due.length === 1) {
        const [{ event, daysBefore }] = due;

        return daysBefore === 0
            ? `🔪 Today: ${event.name}`
            : `🔪 ${describeCountdown(daysBefore)}: ${event.name}`;
    }

    return `🔪 ${due.length} Chopped offseason dates coming up`;
}

function buildBody(due, schedule, siteUrl) {
    const lines = [];
    const html = [`<h2 style="margin:0 0 16px">${escapeHtml(schedule.title)}</h2>`];

    for (const { event, daysBefore } of due) {
        lines.push(headline(daysBefore, event));
        lines.push(formatEventDate(event.date));

        html.push(
            `<div style="margin:0 0 20px;padding:14px 16px;border-left:4px solid ${
                daysBefore === 0 ? "#dc2626" : "#f59e0b"
            };background:#f8fafc">`,
            `<div style="font-weight:700;font-size:16px">${escapeHtml(headline(daysBefore, event))}</div>`,
            `<div style="color:#475569;margin-top:4px">${escapeHtml(formatEventDate(event.date))}</div>`
        );

        if (event.description) {
            lines.push(event.description);
            html.push(
                `<div style="margin-top:8px">${escapeHtml(event.description)}</div>`
            );
        }

        if (event.link) {
            lines.push(event.link);
            html.push(
                `<div style="margin-top:8px"><a href="${escapeHtml(event.link)}">${escapeHtml(event.link)}</a></div>`
            );
        }

        lines.push("");
        html.push("</div>");
    }

    const upcoming = schedule.events.filter(
        (event) => event.daysUntil > 0 && !due.some((item) => item.event.id === event.id)
    );

    if (upcoming.length > 0) {
        lines.push("Also on the calendar:");
        html.push(`<p style="margin:24px 0 8px;font-weight:700">Also on the calendar</p><ul>`);

        for (const event of upcoming.slice(0, 5)) {
            const line = `  ${formatEventDate(event.date)} — ${event.name} (${describeCountdown(event.daysUntil).toLowerCase()})`;

            lines.push(line);
            html.push(`<li>${escapeHtml(line.trim())}</li>`);
        }

        lines.push("");
        html.push("</ul>");
    }

    if (siteUrl) {
        lines.push(`Dashboard: ${siteUrl}`);
        html.push(
            `<p style="margin-top:24px"><a href="${escapeHtml(siteUrl)}">Open the Chopped dashboard</a></p>`
        );
    }

    return { text: lines.join("\n"), html: html.join("\n") };
}

async function send({ subject, text, html, recipients }) {
    const user = process.env.GMAIL_USER;
    const pass = process.env.GMAIL_APP_PASSWORD;

    if (!user || !pass) {
        throw new Error("GMAIL_USER and GMAIL_APP_PASSWORD must both be set.");
    }

    // Imported lazily so --dry-run and the rest of the repo stay dependency free.
    const { default: nodemailer } = await import("nodemailer");

    const transport = nodemailer.createTransport({
        host: "smtp.gmail.com",
        port: 465,
        secure: true,
        auth: { user, pass }
    });

    const info = await transport.sendMail({
        from: `"${process.env.NOTIFY_FROM_NAME || "Chopped League"}" <${user}>`,
        // Recipients go in Bcc so nobody's address is exposed to the league.
        to: user,
        bcc: recipients,
        subject,
        text,
        html
    });

    return info.messageId;
}

const raw = await readSchedule();
const today = dateArg || todayInZone(raw?.timezone ?? "America/New_York");
const schedule = buildSchedule(raw, today);
const due = dueReminders(raw, today);

console.log(`Chopped notifier — ${today} (${schedule.timezone})`);

if (due.length === 0) {
    console.log("Nothing due today.");
    process.exit(0);
}

const recipients = (process.env.NOTIFY_TO ?? "")
    .split(",")
    .map((address) => address.trim())
    .filter(Boolean);

const subject = buildSubject(due);
const { text, html } = buildBody(due, schedule, process.env.SITE_URL);

console.log(`Due: ${due.map((item) => `${item.event.id}@${item.daysBefore}d`).join(", ")}`);

if (dryRun) {
    console.log();
    console.log(`To: ${recipients.join(", ") || "(NOTIFY_TO not set)"}`);
    console.log(`Subject: ${subject}`);
    console.log();
    console.log(text);
    process.exit(0);
}

if (recipients.length === 0) {
    throw new Error("NOTIFY_TO is empty, so there is nobody to email.");
}

const messageId = await send({ subject, text, html, recipients });

console.log(`Sent to ${recipients.length} recipient(s): ${messageId}`);
