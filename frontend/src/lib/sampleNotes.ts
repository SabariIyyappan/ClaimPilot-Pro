export interface SampleNote {
  id: string;
  title: string;
  specialty: string;
  summary: string;
  text: string;
}

export const SAMPLE_NOTES: SampleNote[] = [
  {
    id: 'ortho-knee',
    title: 'Knee Injury Follow-Up',
    specialty: 'Orthopedics',
    summary: 'Meniscal tear confirmed on MRI with arthroscopic repair and physical therapy follow-up.',
    text:
      'Patient presented with acute right knee pain. MRI confirmed meniscal tear. Arthroscopic surgery performed, followed by physical therapy. Blood pressure normal. Follow-up scheduled in two weeks.',
  },
  {
    id: 'neuro-headache',
    title: 'Headache and Dizziness',
    specialty: 'Neurology',
    summary: 'Recurrent headaches with dizziness; MRI brain normal; diagnosed as tension-type headache.',
    text:
      'Patient presented with recurrent headaches and dizziness. MRI of the brain was normal. Diagnosed with tension-type headache related to stress. Prescribed lifestyle changes and mild analgesics.',
  },
  {
    id: 'gp-uri',
    title: 'Upper Respiratory Infection',
    specialty: 'Primary Care',
    summary: 'Sore throat, congestion, and low-grade fever with negative rapid strep test.',
    text:
      'Patient presented with a 2 day history of sore throat, mild nasal congestion, and low grade fever. No shortness of breath or chest pain. Lungs clear to auscultation. Rapid strep test negative. Impression: uncomplicated viral upper respiratory infection. Symptomatic care advised with fluids, rest, and over the counter analgesics. Follow up as needed if symptoms persist or worsen.',
  },
  {
    id: 'cardio-angina',
    title: 'Chest Tightness on Exertion',
    specialty: 'Cardiology',
    summary: 'Intermittent exertional chest tightness with ECG showing sinus tachycardia; stress test planned.',
    text:
      'Patient reported intermittent chest tightness and shortness of breath on exertion over the past week. No resting pain. Vital signs stable. Physical exam unremarkable. In office ECG showed sinus tachycardia without acute ischemic changes. Impression: suspected stable exertional angina. Started low dose beta blocker and scheduled outpatient exercise stress test for further evaluation.',
  },
  {
    id: 'fm-uti',
    title: 'Urinary Tract Infection',
    specialty: 'Family Medicine',
    summary: 'Dysuria and urinary frequency with positive leukocyte esterase and nitrites on urinalysis.',
    text:
      'Patient presented with burning sensation during urination and increased urinary frequency for 3 days. No flank pain or fever. Abdomen soft and non tender; no costovertebral angle tenderness. Point of care urinalysis showed positive leukocyte esterase and nitrites. Impression: uncomplicated lower urinary tract infection. Oral antibiotics initiated and hydration encouraged.',
  },
  {
    id: 'gi-ulcer',
    title: 'Epigastric Pain and Ulcer',
    specialty: 'Gastroenterology',
    summary: 'Post-prandial epigastric pain with endoscopy-confirmed duodenal ulcer and H. pylori workup.',
    text:
      'Patient reported several weeks of epigastric abdominal pain, worse after meals, with nausea and two episodes of non bloody vomiting. No weight loss or gastrointestinal bleeding reported. Physical exam showed mild epigastric tenderness without guarding. Upper endoscopy identified a duodenal ulcer; biopsy samples were obtained for Helicobacter pylori testing. Patient was started on proton pump inhibitor therapy and a combination antibiotic regimen pending confirmation of H pylori infection.',
  },
];
