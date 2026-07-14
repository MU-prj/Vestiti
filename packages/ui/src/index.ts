/**
 * Shared UI utilities and (later) React components for Camerino.
 */

/** Format a price amount in minor units (cents) for display. */
export function formatPrice(amountMinor: number, currency: string, locale = "it-IT"): string {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency,
  }).format(amountMinor / 100);
}
