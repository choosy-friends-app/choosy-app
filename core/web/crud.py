from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView
from django.shortcuts import redirect
from core.models import Group, PlanProposal, Plan, GroupMember
from core.forms import GroupForm, PlanProposalForm, PlanForm

class GroupCreateView(LoginRequiredMixin, CreateView):
    model = Group
    form_class = GroupForm
    template_name = 'pages/crear_entidad.html'
    success_url = reverse_lazy('groups')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        # Add the owner as an active member with OWNER role
        self.object.add_member(user=self.request.user, role=GroupMember.Role.OWNER)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Nuevo Grupo'
        context['meta_title'] = 'Crear Grupo'
        return context

class PlanProposalCreateView(LoginRequiredMixin, CreateView):
    model = PlanProposal
    form_class = PlanProposalForm
    template_name = 'pages/crear_entidad.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Crear Propuesta de Plan'
        context['meta_title'] = 'Crear Propuesta'
        return context

class PlanCreateView(LoginRequiredMixin, CreateView):
    model = Plan
    form_class = PlanForm
    template_name = 'pages/crear_entidad.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        # Automatically set the group from the proposal
        form.instance.group = form.instance.proposal.group
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Añadir Opción de Plan'
        context['meta_title'] = 'Crear Plan'
        return context
