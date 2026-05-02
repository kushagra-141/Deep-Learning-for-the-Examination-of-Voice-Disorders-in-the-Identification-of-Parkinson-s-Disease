import { StyleSheet } from "@react-pdf/renderer";

/**
 * Print styles for the prediction PDF report. Colors are hard-coded — react-pdf
 * doesn't see CSS variables, so we mirror the medical-teal palette from
 * `styles/globals.css` here.
 */
export const COLORS = {
  text: "#0f172a",
  muted: "#64748b",
  border: "#e2e8f0",
  card: "#f8fafc",
  primary: "#2c8a7c",
  destructive: "#dc2626",
  warning: "#d97706",
  success: "#16a34a",
  white: "#ffffff",
} as const;

export const reportStyles = StyleSheet.create({
  page: {
    paddingTop: 36,
    paddingBottom: 48,
    paddingHorizontal: 36,
    fontSize: 10,
    fontFamily: "Helvetica",
    color: COLORS.text,
    lineHeight: 1.4,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 18,
    paddingBottom: 10,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  brand: {
    fontSize: 14,
    fontFamily: "Helvetica-Bold",
    color: COLORS.primary,
  },
  brandSub: {
    fontSize: 8,
    color: COLORS.muted,
    marginTop: 2,
  },
  metaBlock: {
    fontSize: 8,
    color: COLORS.muted,
    textAlign: "right",
  },
  metaLine: {
    marginBottom: 1,
  },
  disclaimerCard: {
    marginBottom: 16,
    padding: 10,
    backgroundColor: "#fef3c7",
    borderWidth: 1,
    borderColor: "#fbbf24",
    borderRadius: 4,
  },
  disclaimerTitle: {
    fontSize: 9,
    fontFamily: "Helvetica-Bold",
    color: "#78350f",
    marginBottom: 4,
    textTransform: "uppercase",
    letterSpacing: 1,
  },
  disclaimerText: {
    fontSize: 9,
    color: "#78350f",
    lineHeight: 1.4,
  },
  sectionTitle: {
    fontSize: 11,
    fontFamily: "Helvetica-Bold",
    marginBottom: 6,
    marginTop: 4,
    textTransform: "uppercase",
    letterSpacing: 0.8,
    color: COLORS.muted,
  },
  summaryCard: {
    flexDirection: "row",
    alignItems: "center",
    padding: 14,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 4,
    marginBottom: 16,
  },
  summaryProb: {
    fontSize: 36,
    fontFamily: "Helvetica-Bold",
    marginRight: 16,
  },
  summaryMeta: {
    flex: 1,
  },
  summaryLabel: {
    fontSize: 10,
    fontFamily: "Helvetica-Bold",
    textTransform: "uppercase",
    letterSpacing: 1,
    marginBottom: 2,
  },
  summaryDesc: {
    fontSize: 9,
    color: COLORS.muted,
  },
  riskHigh: { color: COLORS.destructive },
  riskMid: { color: COLORS.warning },
  riskLow: { color: COLORS.success },
  modelRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 4,
  },
  modelName: {
    width: 110,
    fontSize: 9,
    color: COLORS.text,
  },
  modelBarTrack: {
    flex: 1,
    height: 6,
    backgroundColor: COLORS.border,
    borderRadius: 3,
    overflow: "hidden",
    marginHorizontal: 6,
  },
  modelBarFill: {
    height: 6,
    borderRadius: 3,
  },
  modelProb: {
    width: 38,
    fontSize: 9,
    fontFamily: "Helvetica-Bold",
    textAlign: "right",
  },
  shapRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 3,
  },
  shapFeature: {
    width: 110,
    fontSize: 8,
    color: COLORS.text,
  },
  shapBarWrap: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    marginHorizontal: 6,
  },
  shapBarLeft: {
    flex: 1,
    height: 6,
    flexDirection: "row",
    justifyContent: "flex-end",
  },
  shapBarRight: {
    flex: 1,
    height: 6,
  },
  shapBarFill: {
    height: 6,
    borderRadius: 2,
  },
  shapAxis: {
    width: 1,
    height: 8,
    backgroundColor: COLORS.border,
  },
  shapValue: {
    width: 40,
    fontSize: 8,
    fontFamily: "Helvetica-Bold",
    textAlign: "right",
  },
  featureGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    marginTop: 4,
  },
  featureCell: {
    width: "33%",
    paddingVertical: 3,
    paddingRight: 6,
  },
  featureName: {
    fontSize: 8,
    color: COLORS.muted,
  },
  featureValue: {
    fontSize: 9,
    fontFamily: "Helvetica-Bold",
    color: COLORS.text,
  },
  footer: {
    position: "absolute",
    bottom: 24,
    left: 36,
    right: 36,
    flexDirection: "row",
    justifyContent: "space-between",
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    fontSize: 8,
    color: COLORS.muted,
  },
});
