import * as React from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { HelperText } from "@/components/ui/helper-text"
import { FormField } from "@/components/ui/form-field"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Separator } from "@/components/ui/separator"
import { EmptyState } from "@/components/ui/empty-state"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from "@/components/ui/dropdown-menu"
import { Settings, User, LogOut, ChevronDown, Bell, CheckCircle2 } from "lucide-react"

export default function SpecimenPage() {
  return (
    <div className="min-h-screen bg-background text-foreground py-16 px-6 sm:px-12">
      <div className="mx-auto max-w-5xl space-y-16">
        
        {/* Header */}
        <header className="space-y-4">
          <h1 className="font-serif text-4xl font-semibold tracking-tight text-primary">
            CareIntel Design System
          </h1>
          <p className="text-lg text-muted-foreground max-w-[60ch]">
            Neutral typographic and component specimen. Demonstrates the core visual identity, 
            hierarchy, and interactive states. No mock clinical data is presented.
          </p>
        </header>

        <Separator className="bg-border/60" />

        {/* Typography */}
        <section className="space-y-6">
          <header>
            <h2 className="font-serif text-2xl font-semibold tracking-tight text-secondary">Typography</h2>
            <p className="text-sm text-muted-foreground mt-1">Times New Roman scale defining structural hierarchy.</p>
          </header>
          
          <div className="rounded-xl border border-border bg-surface p-8 shadow-xs space-y-8">
            <div className="grid grid-cols-[1fr_3fr] gap-6 border-b border-border/50 pb-6">
              <span className="text-sm font-medium text-muted-foreground">Heading 1</span>
              <div>
                <h1 className="text-3xl font-semibold text-secondary mb-1">Page Title</h1>
                <p className="text-xs text-muted-foreground">text-3xl, semibold, tracking-tight</p>
              </div>
            </div>
            <div className="grid grid-cols-[1fr_3fr] gap-6 border-b border-border/50 pb-6">
              <span className="text-sm font-medium text-muted-foreground">Heading 2</span>
              <div>
                <h2 className="text-2xl font-semibold text-secondary mb-1">Section Heading</h2>
                <p className="text-xs text-muted-foreground">text-2xl, semibold, tracking-tight</p>
              </div>
            </div>
            <div className="grid grid-cols-[1fr_3fr] gap-6 border-b border-border/50 pb-6">
              <span className="text-sm font-medium text-muted-foreground">Heading 3</span>
              <div>
                <h3 className="text-xl font-semibold text-foreground mb-1">Subsection Heading</h3>
                <p className="text-xs text-muted-foreground">text-xl, semibold</p>
              </div>
            </div>
            <div className="grid grid-cols-[1fr_3fr] gap-6 border-b border-border/50 pb-6">
              <span className="text-sm font-medium text-muted-foreground">Heading 4</span>
              <div>
                <h4 className="text-lg font-semibold text-foreground mb-1">Card or Group Title</h4>
                <p className="text-xs text-muted-foreground">text-lg, semibold</p>
              </div>
            </div>
            <div className="grid grid-cols-[1fr_3fr] gap-6 border-b border-border/50 pb-6">
              <span className="text-sm font-medium text-muted-foreground">Body Text</span>
              <div className="max-w-[70ch]">
                <p className="text-base text-foreground mb-2 leading-relaxed">
                  The primary font is Times New Roman. It establishes a premium, trustworthy healthcare aesthetic. 
                  The text has a constrained prose width to maintain readability across large screens.
                </p>
                <p className="text-xs text-muted-foreground">text-base, normal, leading-relaxed</p>
              </div>
            </div>
            <div className="grid grid-cols-[1fr_3fr] gap-6">
              <span className="text-sm font-medium text-muted-foreground">Small Text</span>
              <div>
                <p className="text-sm text-foreground mb-1">Used for helper text, timestamps, and secondary descriptions.</p>
                <p className="text-xs text-muted-foreground">text-sm, normal</p>
              </div>
            </div>
          </div>
        </section>

        {/* Buttons */}
        <section className="space-y-6">
          <header>
            <h2 className="font-serif text-2xl font-semibold tracking-tight text-secondary">Interactive Controls</h2>
            <p className="text-sm text-muted-foreground mt-1">Actions map strictly to semantic importance.</p>
          </header>
          
          <div className="rounded-xl border border-border bg-surface p-8 shadow-xs">
            <div className="grid grid-cols-[1fr_3fr] gap-6 mb-8">
              <span className="text-sm font-medium text-muted-foreground">Primary</span>
              <div className="flex flex-wrap gap-4">
                <Button variant="default">Save Record</Button>
                <Button variant="default" disabled>Save Record (Disabled)</Button>
              </div>
            </div>
            
            <div className="grid grid-cols-[1fr_3fr] gap-6 mb-8">
              <span className="text-sm font-medium text-muted-foreground">Secondary</span>
              <div className="flex flex-wrap gap-4">
                <Button variant="secondary">View Details</Button>
                <Button variant="outline">Cancel Action</Button>
                <Button variant="ghost">Dismiss</Button>
              </div>
            </div>

            <div className="grid grid-cols-[1fr_3fr] gap-6 mb-8">
              <span className="text-sm font-medium text-muted-foreground">Destructive</span>
              <div className="flex flex-wrap gap-4">
                <Button variant="destructive">Delete Record</Button>
              </div>
            </div>

            <div className="grid grid-cols-[1fr_3fr] gap-6">
              <span className="text-sm font-medium text-muted-foreground">Sizes & Icons</span>
              <div className="flex flex-wrap items-center gap-4">
                <Button variant="outline" size="sm">Small Size</Button>
                <Button variant="default" size="default">Standard Size</Button>
                <Button variant="secondary" size="lg">Large Target</Button>
                <Button variant="ghost" size="icon" aria-label="Settings"><Settings className="size-5" /></Button>
              </div>
            </div>
          </div>
        </section>

        {/* Badges & Status */}
        <section className="space-y-6">
          <header>
            <h2 className="font-serif text-2xl font-semibold tracking-tight text-secondary">Semantic Status</h2>
            <p className="text-sm text-muted-foreground mt-1">Colors carry precise meaning and never serve solely decorative purposes.</p>
          </header>
          
          <div className="flex flex-wrap gap-4 rounded-xl border border-border bg-surface p-8 shadow-xs">
            <Badge variant="neutral">Draft / Neutral</Badge>
            <Badge variant="info">In Review / Info</Badge>
            <Badge variant="success">Completed / Verified</Badge>
            <Badge variant="warning">Action Required</Badge>
            <Badge variant="error">Critical Flag</Badge>
            <Badge variant="outline">Label</Badge>
          </div>
        </section>

        {/* Forms */}
        <section className="space-y-6">
          <header>
            <h2 className="font-serif text-2xl font-semibold tracking-tight text-secondary">Form Inputs</h2>
            <p className="text-sm text-muted-foreground mt-1">Accessible, structured data collection patterns.</p>
          </header>

          <div className="grid gap-8 md:grid-cols-2 rounded-xl border border-border bg-surface p-8 shadow-xs">
            <FormField>
              <Label htmlFor="input-default">First Name</Label>
              <Input id="input-default" placeholder="Enter given name" />
              <HelperText>As it appears on official documents.</HelperText>
            </FormField>

            <FormField>
              <Label htmlFor="input-error">Identifier (Error State)</Label>
              <Input id="input-error" defaultValue="INVALID-992" aria-invalid="true" />
              <HelperText variant="error">This identifier format is not recognized.</HelperText>
            </FormField>

            <FormField>
              <Label>Facility Location</Label>
              <Select>
                <SelectTrigger>
                  <SelectValue placeholder="Select facility..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="fac-1">North Wing Clinic</SelectItem>
                  <SelectItem value="fac-2">South Campus Center</SelectItem>
                  <SelectItem value="fac-3">East Regional Annex</SelectItem>
                </SelectContent>
              </Select>
              <HelperText>Assign to the primary location.</HelperText>
            </FormField>

            <FormField>
              <Label>Assigned Role (Success State)</Label>
              <Select defaultValue="role-1">
                <SelectTrigger className="border-[var(--status-success)] ring-[var(--status-success)]/20">
                  <SelectValue placeholder="Select role..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="role-1">Attending Provider</SelectItem>
                  <SelectItem value="role-2">Specialist Consultant</SelectItem>
                </SelectContent>
              </Select>
              <HelperText variant="success" className="flex items-center gap-1">
                <CheckCircle2 className="size-3" /> Role successfully verified.
              </HelperText>
            </FormField>

            <FormField className="md:col-span-2">
              <Label htmlFor="textarea-desc">Clinical Notes</Label>
              <Textarea id="textarea-desc" placeholder="Provide supplementary context..." className="min-h-32" />
            </FormField>
          </div>
        </section>

        {/* Overlays & Modals */}
        <section className="space-y-6">
          <header>
            <h2 className="font-serif text-2xl font-semibold tracking-tight text-secondary">Surfaces & Overlays</h2>
            <p className="text-sm text-muted-foreground mt-1">Containers that establish depth and focus.</p>
          </header>

          <div className="grid gap-8 md:grid-cols-[1fr_auto]">
            <Card className="shadow-md">
              <CardHeader>
                <CardTitle>Configuration Profile</CardTitle>
                <CardDescription>Review and modify system settings securely.</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-foreground leading-relaxed">
                  Cards provide elevated surface areas for distinct groupings of information. 
                  They utilize soft borders and very subtle shadows to maintain the calm clinical aesthetic.
                </p>
              </CardContent>
              <CardFooter className="justify-end gap-3 pt-6">
                <Button variant="ghost">Discard</Button>
                <Button variant="default">Apply Configuration</Button>
              </CardFooter>
            </Card>

            <div className="rounded-xl border border-border bg-surface p-8 shadow-xs flex flex-col items-center justify-center gap-6 min-w-64">
              <Dialog>
                <DialogTrigger render={<Button variant="secondary" className="w-full" />}>
                  Trigger Dialog
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Confirm Action</DialogTitle>
                    <DialogDescription>
                      Are you sure you want to proceed? This will lock the record and prevent further modification.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="py-2">
                    <p className="text-sm text-foreground">
                      Ensure all required validations have been met before confirming.
                    </p>
                  </div>
                  <DialogFooter showCloseButton>
                    <Button variant="default">Confirm</Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>

              <DropdownMenu>
                <DropdownMenuTrigger render={<Button variant="outline" className="w-full" />}>
                  Action Menu <ChevronDown className="ml-2 size-4 text-muted-foreground" />
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-48">
                  <DropdownMenuItem>
                    <User className="mr-2 size-4" />
                    <span>View Profile</span>
                  </DropdownMenuItem>
                  <DropdownMenuItem>
                    <Settings className="mr-2 size-4" />
                    <span>Preferences</span>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem variant="destructive">
                    <LogOut className="mr-2 size-4" />
                    <span>Secure Sign Out</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>

              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger render={<Button variant="ghost" size="icon" aria-label="Alerts" className="rounded-full" />}>
                    <Bell className="size-5" />
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>3 Unread Alerts</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          </div>
        </section>

        {/* Loading & Empty States */}
        <section className="space-y-6">
          <header>
            <h2 className="font-serif text-2xl font-semibold tracking-tight text-secondary">System Feedback</h2>
            <p className="text-sm text-muted-foreground mt-1">Communicating transition states clearly.</p>
          </header>

          <div className="grid gap-8 md:grid-cols-2">
            <Card className="p-8 shadow-xs">
              <h3 className="font-serif font-semibold text-foreground mb-6">Loading (Skeleton)</h3>
              <div className="flex items-center gap-4">
                <Skeleton className="size-12 rounded-full" />
                <div className="space-y-3 flex-1">
                  <Skeleton className="h-4 w-[85%]" />
                  <Skeleton className="h-4 w-[60%]" />
                </div>
              </div>
              <div className="mt-8 space-y-3">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-[40%]" />
              </div>
            </Card>

            <EmptyState 
              title="No Results Found"
              description="The applied filters did not yield any matching records in the directory."
              action={<Button variant="outline">Clear Filters</Button>}
              className="h-full bg-surface"
            />
          </div>
        </section>

      </div>
    </div>
  )
}
