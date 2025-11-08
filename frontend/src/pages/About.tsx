import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Brain, Shield, Zap, FileText, CheckCircle, Lock } from 'lucide-react';

export default function About() {
  const features = [
    {
      icon: Brain,
      title: 'AI-Powered Coding',
      description: 'Advanced machine learning models analyze clinical notes and suggest accurate ICD-10 and CPT codes with confidence scores.',
    },
    {
      icon: Shield,
      title: 'Blockchain Verification',
      description: 'Every claim is recorded on the Polygon blockchain for immutable audit trails and enhanced security.',
    },
    {
      icon: Zap,
      title: 'Fast & Efficient',
      description: 'Process claims in minutes instead of hours. Our streamlined workflow reduces manual coding time by up to 70%.',
    },
    {
      icon: FileText,
      title: 'CMS-1500 Generation',
      description: 'Automatically generate properly formatted CMS-1500 forms ready for submission to insurance providers.',
    },
    {
      icon: CheckCircle,
      title: 'Human Review',
      description: 'AI suggestions are always reviewed by qualified medical billing professionals before claim submission.',
    },
    {
      icon: Lock,
      title: 'Secure & Compliant',
      description: 'Built with healthcare security standards in mind. All data is encrypted and handled with HIPAA best practices.',
    },
  ];

  const techStack = [
    'React 18',
    'TypeScript',
    'Tailwind CSS',
    'shadcn/ui',
    'Zustand',
    'React Query',
    'Axios',
  ];

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto max-w-6xl px-4 py-12 space-y-16">
        {/* Hero Section */}
        <div className="text-center space-y-4 animate-fade-in">
          <div className="flex justify-center mb-6">
            <div className="rounded-full bg-primary/10 p-4">
              <Brain className="h-16 w-16 text-primary" />
            </div>
          </div>
          <h1>About ClaimPilot Pro</h1>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
            AI-assisted medical coding and claim generation platform designed to streamline 
            healthcare billing workflows while maintaining accuracy and compliance.
          </p>
        </div>

        {/* Mission Statement */}
        <Card className="p-8 bg-accent/30 border-primary/20 animate-fade-in">
          <h2 className="mb-4">Our Mission</h2>
          <p className="text-lg leading-relaxed text-muted-foreground">
            ClaimPilot Pro was built to empower medical billing professionals with cutting-edge AI technology 
            while keeping the human expertise at the center of the process. We believe that automation should 
            assist, not replace, the critical thinking and medical knowledge that billing specialists bring to 
            their work every day.
          </p>
        </Card>

        {/* Features Grid */}
        <div className="space-y-6 animate-fade-in">
          <h2 className="text-center">Key Features</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <Card key={feature.title} className="p-6 hover:shadow-lg transition-shadow">
                  <div className="space-y-3">
                    <div className="rounded-lg bg-primary/10 w-12 h-12 flex items-center justify-center">
                      <Icon className="h-6 w-6 text-primary" />
                    </div>
                    <h3 className="text-xl font-semibold">{feature.title}</h3>
                    <p className="text-base leading-relaxed text-muted-foreground">
                      {feature.description}
                    </p>
                  </div>
                </Card>
              );
            })}
          </div>
        </div>

        {/* How It Works */}
        <div className="space-y-6 animate-fade-in">
          <h2 className="text-center">How It Works</h2>
          <Card className="p-8">
            <div className="space-y-6">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                  1
                </div>
                <div>
                  <h3 className="font-semibold mb-2">Upload Clinical Notes</h3>
                  <p className="text-muted-foreground">
                    Drop a PDF, image, or paste text from your electronic health record system.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                  2
                </div>
                <div>
                  <h3 className="font-semibold mb-2">AI Analyzes & Suggests</h3>
                  <p className="text-muted-foreground">
                    Our AI identifies medical entities and suggests appropriate ICD-10 and CPT codes with confidence scores and reasoning.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                  3
                </div>
                <div>
                  <h3 className="font-semibold mb-2">Review & Approve</h3>
                  <p className="text-muted-foreground">
                    You review suggestions, edit descriptions, add manual codes, and set the claim amount.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                  4
                </div>
                <div>
                  <h3 className="font-semibold mb-2">Sign & Generate</h3>
                  <p className="text-muted-foreground">
                    Certify the claim and generate a CMS-1500 form with blockchain verification for audit trails.
                  </p>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Technology Stack */}
        <div className="space-y-6 animate-fade-in">
          <h2 className="text-center">Built With Modern Technology</h2>
          <Card className="p-8">
            <div className="space-y-4">
              <p className="text-lg text-muted-foreground text-center">
                ClaimPilot Pro is built using cutting-edge web technologies to ensure 
                speed, reliability, and an excellent user experience.
              </p>
              <div className="flex flex-wrap justify-center gap-3 pt-4">
                {techStack.map((tech) => (
                  <Badge key={tech} variant="secondary" className="text-base px-4 py-2">
                    {tech}
                  </Badge>
                ))}
              </div>
            </div>
          </Card>
        </div>

        {/* Compliance Note */}
        <Card className="p-8 bg-muted/30 animate-fade-in">
          <div className="space-y-3 text-center">
            <div className="flex justify-center">
              <Shield className="h-12 w-12 text-primary" />
            </div>
            <h3 className="font-semibold">Security & Compliance</h3>
            <p className="text-base leading-relaxed text-muted-foreground max-w-2xl mx-auto">
              This is a demonstration platform. For production use, ensure compliance with HIPAA regulations, 
              medical coding standards (ICD-10, CPT), insurance industry requirements, and blockchain 
              compliance in your jurisdiction. Always consult with legal and compliance professionals before 
              processing real patient data.
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
}
