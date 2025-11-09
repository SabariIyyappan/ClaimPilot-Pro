import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Download } from 'lucide-react';
import type { CodeSuggestion } from '@/lib/types';
import { downloadCms1500, deriveCms1500 } from '@/lib/api';
import { toast } from 'sonner';

interface Props {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  approved: CodeSuggestion[];
  text: string;
}

export function CMS1500Dialog({ open, onOpenChange, approved, text }: Props) {
  const [patientName, setPatientName] = useState('');
  const [patientId, setPatientId] = useState('');
  const [providerName, setProviderName] = useState('');
  const [dateOfService, setDateOfService] = useState('');
  const [patientDob, setPatientDob] = useState('');
  const [patientSex, setPatientSex] = useState('');
  const [patientAddress, setPatientAddress] = useState('');
  const [placeOfService, setPlaceOfService] = useState('');
  const [referringNpi, setReferringNpi] = useState('');
  const [diagPtrInputs, setDiagPtrInputs] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  // Autofill from backend-derived fields when dialog opens
  useEffect(() => {
    if (!open) return;
    (async () => {
      try {
        const d = await deriveCms1500(text || '');
        setPatientName(d.patient_name || '');
        setPatientId(d.patient_id || '');
        setProviderName(d.provider_name || '');
        setDateOfService(d.date_of_service || '');
        setPatientDob(d.patient_dob || '');
        setPatientSex(d.patient_sex || '');
        setPatientAddress(d.patient_address || '');
        setPlaceOfService(d.place_of_service || '');
        setReferringNpi(d.referring_npi || '');
      } catch {}
      // default diag pointers to "1"
      setDiagPtrInputs(approved.map(() => '1'));
    })();
  }, [open, text, approved]);

  const handleDownload = async () => {
    try {
      setLoading(true);
      const blob = await downloadCms1500({
        approved,
        text,
        patient_name: patientName || undefined,
        patient_id: patientId || undefined,
        provider_name: providerName || undefined,
        date_of_service: dateOfService || undefined,
        patient_dob: patientDob || undefined,
        patient_sex: patientSex || undefined,
        patient_address: patientAddress || undefined,
        place_of_service: placeOfService || undefined,
        referring_npi: referringNpi || undefined,
        diag_pointers: diagPtrInputs.map((s) =>
          (s || '1')
            .split(',')
            .map((x) => parseInt(x.trim(), 10))
            .filter((n) => Number.isFinite(n) && n >= 1)
        ),
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'cms1500_filled.pdf';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast.success('CMS-1500 downloaded');
    } catch (e: any) {
      toast.error(e?.message || 'Failed to generate CMS-1500');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>Review & Generate CMS-1500</DialogTitle>
          <DialogDescription>
            Fill patient and provider details. We will generate a CMS-1500 PDF with neatly boxed fields.
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div>
              <Label>Patient Name</Label>
              <Input value={patientName} onChange={(e) => setPatientName(e.target.value)} placeholder="e.g., John A. Doe" />
            </div>
            <div>
              <Label>Patient ID</Label>
              <Input value={patientId} onChange={(e) => setPatientId(e.target.value)} placeholder="e.g., MRN-123456" />
            </div>
            <div>
              <Label>Provider Name</Label>
              <Input value={providerName} onChange={(e) => setProviderName(e.target.value)} placeholder="e.g., Dr. Emily Carter" />
            </div>
            <div>
              <Label>Date of Service</Label>
              <Input type="date" value={dateOfService} onChange={(e) => setDateOfService(e.target.value)} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Patient DOB</Label>
                <Input type="date" value={patientDob} onChange={(e) => setPatientDob(e.target.value)} />
              </div>
              <div>
                <Label>Sex</Label>
                <Input placeholder="M/F" value={patientSex} onChange={(e) => setPatientSex(e.target.value)} />
              </div>
            </div>
            <div>
              <Label>Patient Address</Label>
              <Input value={patientAddress} onChange={(e) => setPatientAddress(e.target.value)} placeholder="Street, City, State ZIP" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Place of Service (POS)</Label>
                <Input placeholder="e.g., 11" value={placeOfService} onChange={(e) => setPlaceOfService(e.target.value)} />
              </div>
              <div>
                <Label>Referring Provider NPI</Label>
                <Input placeholder="e.g., 1234567890" value={referringNpi} onChange={(e) => setReferringNpi(e.target.value)} />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Diagnosis Pointers (per CPT row)</Label>
              <div className="space-y-2">
                {approved.slice(0, 10).map((p, idx) => (
                  <div key={idx} className="grid grid-cols-12 items-center gap-2 text-sm">
                    <div className="col-span-5 truncate">{p.code} – {p.description}</div>
                    <div className="col-span-7">
                      <Input
                        value={diagPtrInputs[idx] || ''}
                        onChange={(e) => {
                          const next = [...diagPtrInputs];
                          next[idx] = e.target.value;
                          setDiagPtrInputs(next);
                        }}
                        placeholder="e.g., 1 or 1,3"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Simple visual layout approximating CMS-1500 boxes */}
          <Card className="p-4 space-y-3">
            <div className="grid grid-cols-12 gap-1 text-xs">
              <div className="col-span-12 font-semibold">Preview Layout</div>
              <div className="col-span-7 border p-2">1. Patient Name<br/>{patientName || '—'}</div>
              <div className="col-span-5 border p-2">2. Patient ID<br/>{patientId || '—'}</div>
              <div className="col-span-7 border p-2">3. Provider Name<br/>{providerName || '—'}</div>
              <div className="col-span-5 border p-2">4. Date of Service<br/>{dateOfService || '—'}</div>
              <div className="col-span-6 border p-2">5. Patient DOB<br/>{patientDob || '—'}</div>
              <div className="col-span-6 border p-2">6. Sex<br/>{patientSex || '—'}</div>
              <div className="col-span-12 border p-2">7. Patient Address<br/>{patientAddress || '—'}</div>
              <div className="col-span-6 border p-2">POS<br/>{placeOfService || '—'}</div>
              <div className="col-span-6 border p-2">Referring NPI<br/>{referringNpi || '—'}</div>
              <div className="col-span-12 border p-2">Approved Codes ({approved.length}) – included in generated PDF</div>
            </div>
            <p className="text-[11px] text-muted-foreground">The PDF generator uses these values to fill a CMS-1500 style form.</p>
          </Card>
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>Close</Button>
          <Button onClick={handleDownload} disabled={loading}>
            <Download className="mr-2 h-4 w-4" />
            {loading ? 'Generating…' : 'Download Filled CMS-1500'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

