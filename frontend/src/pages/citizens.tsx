import { Trophy, TrendingUp, Users as UsersIcon, Calendar } from "lucide-react";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Input } from "../components/ui/input";
import { Progress } from "../components/ui/progress";
import { Avatar, AvatarFallback } from "../components/ui/avatar";
import { CreateCitizenDialog } from "../components/create-citizen-dialog";
import { useState } from "react";
import CitizenDetailDialog from "../components/citizen-detail-dialog";
import { ConsultationDetailDialog } from "../components/consultation-detail-dialog";
import { useQuery } from "@tanstack/react-query";
import { Skeleton } from "../components/ui/skeleton";
import { Badge } from "../components/ui/badge";

interface Citizen {
  id: number;
  name: string;
  address: string | null;
  phone: string | null;
  email: string | null;
  engagementScore: number;
  mobilityPrefs: any;
}

interface Consultation {
  id: number;
  citizenId: number;
  citizenName: string;
  date: string;
  topic: string;
  participationMode: string;
  heure?: string;
}

export default function Citizens() {
  const [selectedCitizen, setSelectedCitizen] = useState < Citizen | null > (null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [selectedConsultation, setSelectedConsultation] = useState < Consultation | null > (null);
  const [consultationDetailOpen, setConsultationDetailOpen] = useState(false);
  const [consultationSearchFilter, setConsultationSearchFilter] = useState("");
  const { data: citizens, isLoading: citizensLoading } = useQuery < Citizen[] > ({
    queryKey: ["/api/citizens"],
  });

  const { data: topCitizens, isLoading: topLoading } = useQuery < Citizen[] > ({
    queryKey: ["/api/citizens/top"],
  });

  const { data: consultations, isLoading: consultationsLoading } = useQuery < Consultation[] > ({
    queryKey: ["/api/consultations"],
  });

  const recentConsultations = (consultations || []).filter((consultation) => {
    if (!consultationSearchFilter.trim()) return true;
    return consultation.citizenName.toLowerCase().includes(consultationSearchFilter.toLowerCase());
  });
  const avgScore = citizens?.length ? Math.round(citizens.reduce((sum, c) => sum + c.engagementScore, 0) / citizens.length) : 0;
  return (
    <div className="flex-1 overflow-auto">
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Engagement Citoyen</h1>
            <p className="text-muted-foreground mt-1">
              Suivi de la participation et des initiatives écologiques
            </p>
          </div>
          <div className="flex items-center gap-2">
            <CreateCitizenDialog />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="hover-elevate">
            <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Citoyens Inscrits
              </CardTitle>
              <UsersIcon className="w-4 h-4 text-primary" />
            </CardHeader>
            <CardContent>
              {citizensLoading ? (
                <Skeleton className="h-10 w-20" />
              ) : (
                <>
                  <div className="text-3xl font-bold font-mono" data-testid="text-total-citizens">{citizens?.length || 0}</div>
                  <p className="text-xs text-muted-foreground mt-1">Participants actifs</p>
                </>
              )}
            </CardContent>
          </Card>

          <Card className="hover-elevate">
            <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Score Moyen
              </CardTitle>
              <TrendingUp className="w-4 h-4 text-primary" />
            </CardHeader>
            <CardContent>
              {citizensLoading ? (
                <Skeleton className="h-10 w-20" />
              ) : (
                <>
                  <div className="text-3xl font-bold font-mono" data-testid="text-avg-score">{avgScore}</div>
                  <p className="text-xs text-muted-foreground mt-1">Sur 100 points</p>
                </>
              )}
            </CardContent>
          </Card>

          <Card className="hover-elevate">
            <CardHeader className="flex flex-row items-center justify-between gap-2 space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Consultations
              </CardTitle>
              <Calendar className="w-4 h-4 text-primary" />
            </CardHeader>
            <CardContent>
              {consultationsLoading ? (
                <Skeleton className="h-10 w-20" />
              ) : (
                <>
                  <div className="text-3xl font-bold font-mono" data-testid="text-total-consultations">{consultations?.length || 0}</div>
                  <p className="text-xs text-muted-foreground mt-1">Total</p>
                </>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Trophy className="w-5 h-5 text-amber-500" />
                  Top Contributeurs
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              {topLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : topCitizens && topCitizens.length > 0 ? (
                <div className="space-y-3 max-h-[350px] overflow-y-auto pr-2" data-testid="list-top-citizens">
                  {topCitizens.map((citizen, index) => (
                    <div
                      key={citizen.id}
                      role="button"
                      tabIndex={0}
                      onClick={() => { setSelectedCitizen(citizen); setDetailOpen(true); }}
                      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { setSelectedCitizen(citizen); setDetailOpen(true); } }}
                      className="flex items-center gap-4 p-3 border rounded-md hover-elevate cursor-pointer"
                    >
                      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary font-bold">
                        {index + 1}
                      </div>
                      <Avatar>
                        <AvatarFallback className="bg-primary/20 text-primary">
                          {citizen.name.split(' ').map(n => n[0]).join('').substring(0, 2)}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm">{citizen.name}</p>
                        <p className="text-xs text-muted-foreground truncate">{citizen.address}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-lg font-mono">{citizen.engagementScore}</p>
                        <Progress value={citizen.engagementScore} className="w-16 h-1.5 mt-1" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-muted-foreground text-center py-12">
                  <Trophy className="w-12 h-12 mx-auto mb-4 text-muted-foreground/50" />
                  <p className="font-medium">Aucun citoyen inscrit</p>
                  <p className="text-xs mt-1">Le classement apparaîtra ici</p>
                </div>
              )}
            </CardContent>
          </Card>

          <CitizenDetailDialog open={detailOpen} onOpenChange={setDetailOpen} citizen={selectedCitizen} />

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between gap-2">
                <CardTitle>Consultations Récentes</CardTitle>
                <Input
                  placeholder="Filtrer par citoyen..."
                  className="w-48"
                  value={consultationSearchFilter}
                  onChange={(e) => setConsultationSearchFilter(e.target.value)}
                  data-testid="input-search-consultations"
                />
              </div>
            </CardHeader>
            <CardContent>
              {consultationsLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <Skeleton key={i} className="h-20 w-full" />
                  ))}
                </div>
              ) : recentConsultations.length > 0 ? (
                <div className="space-y-3 max-h-[350px] overflow-y-auto pr-2" data-testid="list-recent-consultations">
                  {recentConsultations.map((consultation) => (
                    <div
                      key={consultation.id}
                      role="button"
                      tabIndex={0}
                      onClick={() => { setSelectedConsultation(consultation); setConsultationDetailOpen(true); }}
                      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { setSelectedConsultation(consultation); setConsultationDetailOpen(true); } }}
                      className="p-4 border rounded-md hover-elevate cursor-pointer"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1">
                          <p className="font-medium text-sm">{consultation.topic}</p>
                          <p className="text-xs text-muted-foreground mt-1">
                            {consultation.participationDate ? new Date(consultation.participationDate).toLocaleDateString('fr-FR') : '-'}
                          </p>
                        </div>
                        <Badge variant="secondary" className="text-xs">
                          {consultation.participationMode || consultation.mode || '-'}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-muted-foreground text-center py-12">
                  <Calendar className="w-12 h-12 mx-auto mb-4 text-muted-foreground/50" />
                  <p className="font-medium">Aucune consultation</p>
                  <p className="text-xs mt-1">Les participations apparaîtront ici</p>
                </div>
              )}
            </CardContent>
          </Card>

          <ConsultationDetailDialog
            open={consultationDetailOpen}
            onOpenChange={setConsultationDetailOpen}
            consultation={selectedConsultation}
          />
        </div>
      </div>
    </div>
  );
}
