"use client";

import { ChangeEvent, FormEvent, useState } from "react";
import Link from "next/link";
import { AlertCircle, CheckCircle2, FileUp, Loader2, Sparkles } from "lucide-react";
import Navbar from "../../components/Navbar";
import { AiCaseExtraction, CaseCreatePayload, ExtractedEntityItem, extractAiCaseIntake, registerAiAssistedCase } from "../../lib/api";

const steps = ["Upload Document", "AI/OCR Processing", "Extract Case Information", "Officer Review", "Confirm & Register"];
const acceptedTypes = ".pdf,.jpg,.jpeg,.png";

export default function AiCaseRegistrationPage() {
  const [file, setFile] = useState<File | null>(null);
  const [extraction, setExtraction] = useState<AiCaseExtraction | null>(null);
  const [processing, setProcessing] = useState(false);
  const [registering, setRegistering] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [entities, setEntities] = useState<ExtractedEntityItem[]>([]);
  const [form, setForm] = useState<CaseCreatePayload>({ case_number: "", title: "", description: "", crime_type: "", status: "UNDER_INVESTIGATION", priority: "HIGH", police_station: "", district: "", state: "", location: "", incident_date: "", act_section: "", registration_method: "AI_ASSISTED" });

  const handleFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0];
    if (!selected) return;
    setFile(selected); setExtraction(null); setError(null); setProcessing(true);
    try {
      const result = await extractAiCaseIntake(selected);
      setExtraction(result);
      setEntities(result.entities);
      const fields = result.fields;
      setForm((current) => ({
        ...current,
        case_number: fields.case_number || "", police_station: fields.police_station || "",
        district: fields.district || "", state: fields.state || "", location: fields.location || "",
        crime_type: fields.crime_type || "", description: fields.description || "",
        incident_date: fields.incident_date || "", act_section: fields.act_section || "", title: fields.title || fields.crime_type || "",
      }));
    } catch (err: any) { setError(err.message || "The document could not be processed."); }
    finally { setProcessing(false); }
  };

  const update = (key: keyof CaseCreatePayload, value: string) => setForm((current) => ({ ...current, [key]: value }));
  const confirm = async (event: FormEvent) => {
    event.preventDefault();
    if (!file || !extraction) return;
    if (!form.case_number || !form.title || !form.crime_type) { setError("Case number, title, and crime type must be verified before registration."); return; }
    setError(null); setRegistering(true);
    try {
      const registered = await registerAiAssistedCase(file, form, { ...extraction.metadata, reviewed_entities: entities });
      window.location.assign(`/cases/${registered.id}`);
    } catch (err: any) { setError(err.message || "Case registration failed. The case has not been registered; please retry."); }
    finally { setRegistering(false); }
  };

  return <div className="min-h-screen flex flex-col bg-black text-ink">
    <Navbar />
    <main className="flex-1 max-w-5xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
      <div className="border-b border-hairline pb-5">
        <div className="flex items-center gap-2 text-zinc-300"><Sparkles className="w-4 h-4" /><span className="text-xs font-mono uppercase tracking-wider">Secure intake</span></div>
        <h1 className="mt-2 text-xl font-semibold tracking-tight text-white">AI-Assisted Case Registration</h1>
        <p className="mt-1 text-xs text-mute">Upload an FIR, complaint, or case document and let AI extract the case information for officer verification.</p>
      </div>

      <ol className="grid grid-cols-1 sm:grid-cols-5 gap-2" aria-label="Registration workflow">
        {steps.map((step, index) => <li key={step} className={`border rounded-sm px-3 py-2 text-[10px] font-mono uppercase ${index === (extraction ? 3 : 0) ? "border-zinc-500 bg-zinc-900 text-white" : "border-hairline bg-canvas-elevated text-mute"}`}>{index + 1}. {step}</li>)}
      </ol>

      {error && <div className="p-3 rounded-sm bg-red-950/30 border border-red-900/50 flex gap-2 text-xs text-red-200"><AlertCircle className="w-4 h-4 shrink-0" /><div>{error}<div className="mt-2"><Link href="/dashboard" className="underline text-red-100">Switch to manual registration</Link></div></div></div>}

      {!extraction && <section className="bg-canvas-elevated border border-hairline rounded-md p-6">
        <label className="border border-dashed border-zinc-700 hover:border-zinc-500 transition rounded-sm min-h-52 flex flex-col items-center justify-center text-center cursor-pointer px-4">
          {processing ? <Loader2 className="w-7 h-7 animate-spin text-white" /> : <FileUp className="w-7 h-7 text-zinc-300" />}
          <span className="mt-3 text-sm font-medium text-white">{processing ? "Processing document with OCR and AI…" : "Upload FIR, complaint, or case document"}</span>
          <span className="mt-1 text-xs text-mute">PDF, JPG, JPEG, or PNG — only formats supported by the secure document service.</span>
          <input className="sr-only" type="file" accept={acceptedTypes} onChange={handleFile} disabled={processing} />
        </label>
      </section>}

      {extraction && <form onSubmit={confirm} className="space-y-5">
        <section className="p-3 rounded-sm bg-amber-950/25 border border-amber-900/60 text-xs text-amber-100 flex gap-2"><AlertCircle className="w-4 h-4 shrink-0 text-amber-400" />AI-generated information must be reviewed and verified by the investigating officer before registration.</section>
        <section className="bg-canvas-elevated border border-hairline rounded-md p-5 space-y-4">
          <div className="flex justify-between gap-3 border-b border-hairline pb-3"><div><h2 className="text-sm font-semibold text-white">Extracted Case Information</h2><p className="text-[11px] text-mute">AI-extracted from {extraction.filename}. All values below are editable.</p></div><span className="text-[10px] font-mono text-zinc-400">AI EXTRACTED</span></div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <Field label="FIR / Case Number *" value={form.case_number} onChange={(v) => update("case_number", v)} />
            <Field label="Case Title *" value={form.title} onChange={(v) => update("title", v)} />
            <Field label="Police Station" value={form.police_station || ""} onChange={(v) => update("police_station", v)} />
            <Field label="District" value={form.district || ""} onChange={(v) => update("district", v)} />
            <Field label="Incident Location" value={form.location || ""} onChange={(v) => update("location", v)} />
            <Field label="Crime Type / Nature of Offence *" value={form.crime_type} onChange={(v) => update("crime_type", v)} />
            <Field label="Applicable Legal Sections" value={form.act_section || ""} onChange={(v) => update("act_section", v)} />
            <Field label="Date of Incident" type="date" value={form.incident_date || ""} onChange={(v) => update("incident_date", v)} />
          </div>
          <div><label className="block text-zinc-300 font-medium mb-1 text-xs">Incident Description</label><textarea rows={7} value={form.description || ""} onChange={(e) => update("description", e.target.value)} className="w-full bg-zinc-950 border border-hairline rounded-sm px-3 py-2 text-white focus:outline-none focus:border-zinc-500" /></div>
          {entities.length > 0 && <div className="text-xs"><p className="text-zinc-300 font-medium mb-2">Other extracted entities</p><div className="grid grid-cols-1 md:grid-cols-2 gap-3">{entities.map((entity, index) => <div key={`${entity.entity_type}-${index}`}><label className="block text-[10px] font-mono text-mute mb-1">{entity.entity_type}</label><input value={entity.entity_value} onChange={(e) => setEntities((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, entity_value: e.target.value, normalized_value: e.target.value } : item))} className="w-full bg-zinc-950 border border-hairline rounded-sm px-3 py-1.5 text-white focus:outline-none focus:border-zinc-500" /></div>)}</div></div>}
          {typeof extraction.metadata.ocr_confidence === "number" && <p className="text-[10px] font-mono text-mute">OCR confidence returned by the processing engine: {Math.round((extraction.metadata.ocr_confidence as number) * 100)}%</p>}
        </section>
        <div className="flex flex-wrap justify-end gap-2"><button type="button" onClick={() => { setExtraction(null); setFile(null); }} className="px-3.5 py-1.5 text-xs rounded-sm border border-hairline text-zinc-300 hover:bg-zinc-900">Cancel</button><button type="button" onClick={() => document.getElementById("case-review")?.scrollIntoView()} className="px-3.5 py-1.5 text-xs rounded-sm border border-hairline text-zinc-300 hover:bg-zinc-900">Edit &amp; Review</button><button type="submit" disabled={registering} className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-medium rounded-sm bg-white text-black hover:bg-zinc-200 disabled:opacity-50">{registering ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle2 className="w-3.5 h-3.5" />}Confirm &amp; Register Case</button></div>
      </form>}
    </main>
  </div>;
}

function Field({ label, value, onChange, type = "text", readOnly = false }: { label: string; value: string; onChange: (value: string) => void; type?: string; readOnly?: boolean }) {
  return <div><label className="block text-zinc-300 font-medium mb-1">{label}</label><input type={type} value={value} onChange={(e) => onChange(e.target.value)} readOnly={readOnly} className="w-full bg-zinc-950 border border-hairline rounded-sm px-3 py-1.5 text-white focus:outline-none focus:border-zinc-500 read-only:text-zinc-400" /></div>;
}
