
package com.moneyagent;

import android.app.Activity;
import android.app.AlertDialog;
import android.os.Bundle;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.content.SharedPreferences;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONObject;

import java.text.NumberFormat;
import java.util.Locale;
import java.util.Currency;
import java.util.Date;
import java.text.SimpleDateFormat;

public class MainActivity extends Activity {

    private final int BG = Color.rgb(15, 23, 42);
    private final int PANEL = Color.rgb(30, 41, 59);
    private final int GREEN = Color.rgb(52, 211, 153);
    private final int WHITE = Color.WHITE;
    private final int MUTED = Color.rgb(180, 190, 205);

    private LinearLayout root;
    private LinearLayout content;
    private SharedPreferences prefs;
    private JSONArray transactions = new JSONArray();
    private JSONArray assets = new JSONArray();
    private JSONArray debts = new JSONArray();
    private double cash = 0;
    private JSONObject agentReport;
    private String agentLoadMessage = "Зареждаме актуалния отчет от агента...";
    private boolean agentLoading = false;

    private final NumberFormat money = createEuroFormat();

    private NumberFormat createEuroFormat() {
        NumberFormat format = NumberFormat.getCurrencyInstance(new Locale("bg", "BG"));
        format.setCurrency(Currency.getInstance("EUR"));
        format.setMinimumFractionDigits(2);
        format.setMaximumFractionDigits(2);
        return format;
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        prefs = getSharedPreferences("money_agent_data", MODE_PRIVATE);
        loadData();
        buildScreen();
    }

    private void loadData() {
        cash = Double.longBitsToDouble(
                prefs.getLong("cash", Double.doubleToLongBits(0)));
        try {
            transactions = new JSONArray(prefs.getString("transactions", "[]"));
            assets = new JSONArray(prefs.getString("assets", "[]"));
            debts = new JSONArray(prefs.getString("debts", "[]"));
        } catch (Exception e) {
            transactions = new JSONArray();
            assets = new JSONArray();
            debts = new JSONArray();
        }
    }

    private void saveData() {
        prefs.edit()
                .putLong("cash", Double.doubleToLongBits(cash))
                .putString("transactions", transactions.toString())
                .putString("assets", assets.toString())
                .putString("debts", debts.toString())
                .apply();
    }

    private void buildScreen() {
        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(BG);

        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(18), dp(24), dp(18), dp(28));
        scroll.addView(root);

        TextView title = text("MONEY AGENT", 27, WHITE, true);
        root.addView(title);

        TextView subtitle = text(
                "Твоят личен финансов помощник", 14, MUTED, false);
        root.addView(subtitle);

        space(root, 22);

        content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        root.addView(content);

        renderDashboard();
        setContentView(scroll);
        refreshAgentReport();
    }

    private void renderDashboard() {
        content.removeAllViews();

        renderAgentPanel();
        section("ЛИЧНИ ФИНАНСИ");

        double income = sumTransactions("Приход");
        double expenses = sumTransactions("Разход");
        double assetTotal = sumItems(assets);
        double debtTotal = sumItems(debts);

        card(content, "НАЛИЧНИ ПАРИ", money.format(cash), GREEN);
        card(content, "ПРИХОДИ ОБЩО", money.format(income), WHITE);
        card(content, "РАЗХОДИ ОБЩО", money.format(expenses),
                Color.rgb(251, 146, 60));
        card(content, "АКТИВИ", money.format(assetTotal), WHITE);
        card(content, "ДЪЛГОВЕ", money.format(debtTotal),
                Color.rgb(248, 113, 113));

        TextView net = text("Нетна стойност: " +
                money.format(cash + assetTotal - debtTotal),
                19, GREEN, true);
        net.setPadding(4, dp(16), 4, dp(16));
        content.addView(net);

        section("ДЕЙСТВИЯ");

        actionButton("＋ Добави приход", v -> addTransaction("Приход"));
        actionButton("－ Добави разход", v -> addTransaction("Разход"));
        actionButton("＋ Добави актив", v -> addItem("Актив"));
        actionButton("＋ Добави дълг", v -> addItem("Дълг"));

        actionButton("📋 История на операциите", v -> showTransactions());
        actionButton("📊 Финансов анализ", v -> showAnalysis());
        actionButton("⚙️ Начална наличност", v -> setCash());

        section("ПОСЛЕДНИ ОПЕРАЦИИ");
        if (transactions.length() == 0) {
            TextView empty = text(
                    "Все още няма операции. Добави първата си операция.",
                    14, MUTED, false);
            content.addView(empty);
        } else {
            int start = Math.max(0, transactions.length() - 5);
            for (int i = transactions.length() - 1; i >= start; i--) {
                JSONObject item = transactions.optJSONObject(i);
                if (item != null) {
                    String type = item.optString("type", "");
                    String name = item.optString("name", "");
                    double amount = item.optDouble("amount", 0);
                    TextView row = text(
                            type + " • " + name + " • " +
                                    money.format(amount),
                            14, WHITE, false);
                    row.setPadding(0, dp(8), 0, dp(8));
                    content.addView(row);
                }
            }
        }

        TextView note = text(
                "Данните се съхраняват локално на този телефон. " +
                "Това е базов помощник, а не свързана банкова услуга.",
                12, MUTED, false);
        note.setPadding(0, dp(24), 0, dp(8));
        content.addView(note);
    }


    private void renderAgentPanel() {
        section("MONEY-AGENT • ОПЕРАТИВЕН ЦЕНТЪР");
        if (agentReport == null) {
            TextView loading = text(agentLoadMessage, 14, MUTED, false);
            loading.setPadding(0, dp(4), 0, dp(10));
            content.addView(loading);
        } else {
            JSONObject quality = agentReport.optJSONObject("quality_control");
            JSONObject analysis = agentReport.optJSONObject("analysis");
            JSONObject pipeline = agentReport.optJSONObject("pipeline");
            JSONObject dealMaker = agentReport.optJSONObject("deal_maker");
            int candidates = quality == null ? 0 : quality.optInt("candidate_count", 0);
            int tracked = pipeline == null ? 0 : pipeline.optInt("tracked_leads", 0);
            int review = analysis == null ? 0 : analysis.optInt("qualified_for_review", 0);
            double revenue = pipeline == null ? 0 : pipeline.optDouble("confirmed_revenue_eur", 0);
            int drafts = dealMaker == null ? 0 : dealMaker.optInt("draft_count", 0);

            card(content, "НОВИ ПУБЛИКАЦИИ ЗА ПРОВЕРКА", String.valueOf(candidates), WHITE);
            card(content, "ЗАПИСИ В CRM", String.valueOf(tracked), WHITE);
            card(content, "ОДОБРЕНИ ЗА ЧОВЕШКИ ПРЕГЛЕД", String.valueOf(review), GREEN);
            card(content, "ПОДГОТВЕНИ ЧЕРНОВИ", String.valueOf(drafts), WHITE);
            card(content, "ПОТВЪРДЕНИ ПРИХОДИ", String.format(Locale.US, "%.2f €", revenue), GREEN);

            TextView status = text(
                    "Статус: " + (analysis == null ? "няма данни" :
                    analysis.optString("status", "неизвестен")) +
                    "\nПоследно обновяване: " + agentReport.optString("generated_at", "неизвестно"),
                    12, MUTED, false);
            status.setPadding(0, dp(4), 0, dp(8));
            content.addView(status);

            JSONArray errors = agentReport.optJSONArray("errors");
            if (errors != null && errors.length() > 0) {
                JSONObject firstError = errors.optJSONObject(0);
                if (firstError != null) {
                    TextView warning = text("Източник с проблем: " +
                            firstError.optString("name", firstError.optString("source", "неизвестен")) +
                            " — " + firstError.optString("error", "грешка"),
                            12, Color.rgb(251, 191, 36), false);
                    warning.setPadding(0, 0, 0, dp(8));
                    content.addView(warning);
                }
            }
        }

        actionButton(agentLoading ? "Обновявам..." : "↻ Обнови данните на агента",
                v -> refreshAgentReport());
        actionButton("👥 Публикации за преглед", v -> showAgentLeads());
        actionButton("💼 Какво продаваме", v -> showCommercialOffer());
        TextView safety = text(
                "Агентът не изпраща съобщения, не харчи пари и не сключва сделки автоматично. Всяко обръщение към клиент изисква човешко одобрение.",
                12, MUTED, false);
        safety.setPadding(0, dp(8), 0, dp(18));
        content.addView(safety);
    }

    private void refreshAgentReport() {
        if (agentLoading) return;
        agentLoading = true;
        agentLoadMessage = "Свързване с Money-agent...";
        if (content != null) renderDashboard();

        new Thread(() -> {
            HttpURLConnection connection = null;
            try {
                URL url = new URL("https://raw.githubusercontent.com/primo12345678/Money-agent/main/report.json");
                connection = (HttpURLConnection) url.openConnection();
                connection.setRequestMethod("GET");
                connection.setConnectTimeout(12000);
                connection.setReadTimeout(12000);
                connection.setUseCaches(false);
                int code = connection.getResponseCode();
                if (code != 200) throw new Exception("HTTP " + code);
                BufferedReader reader = new BufferedReader(
                        new InputStreamReader(connection.getInputStream(), "UTF-8"));
                StringBuilder body = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) body.append(line);
                reader.close();
                JSONObject report = new JSONObject(body.toString());
                runOnUiThread(() -> {
                    agentReport = report;
                    agentLoading = false;
                    agentLoadMessage = "Данните са обновени.";
                    renderDashboard();
                });
            } catch (Exception e) {
                runOnUiThread(() -> {
                    agentLoading = false;
                    agentLoadMessage = "Не успях да заредя отчета. Провери интернет връзката и опитай отново.";
                    if (content != null) renderDashboard();
                });
            } finally {
                if (connection != null) connection.disconnect();
            }
        }).start();
    }

    private void showAgentLeads() {
        if (agentReport == null) {
            toast("Първо обнови данните на агента.");
            return;
        }
        JSONArray opportunities = agentReport.optJSONArray("opportunities");
        StringBuilder details = new StringBuilder();
        if (opportunities == null || opportunities.length() == 0) {
            details.append("В момента няма публикации за преглед.");
        } else {
            for (int i = 0; i < opportunities.length(); i++) {
                JSONObject item = opportunities.optJSONObject(i);
                if (item == null) continue;
                JSONObject analysis = item.optJSONObject("analysis");
                details.append(i + 1).append(". ")
                        .append(item.optString("title", "Без заглавие")).append("\n")
                        .append("Източник: ").append(item.optString("source", "неизвестен")).append("\n")
                        .append("Оценка: ").append(analysis == null ? "няма" :
                                analysis.optInt("opportunity_score", 0)).append("/100\n")
                        .append("Статус: само за човешка проверка\n")
                        .append(item.optString("url", "")).append("\n\n");
            }
        }
        new AlertDialog.Builder(this)
                .setTitle("Публикации за преглед")
                .setMessage(details.toString())
                .setPositiveButton("Затвори", null)
                .show();
    }

    private void showCommercialOffer() {
        JSONObject model = agentReport == null ? null :
                agentReport.optJSONObject("commercial_model");
        JSONObject offer = model == null ? null : model.optJSONObject("offer");
        if (offer == null) {
            toast("Офертата още не е заредена.");
            return;
        }
        JSONArray scope = offer.optJSONArray("scope");
        StringBuilder message = new StringBuilder();
        message.append(offer.optString("name", "Услуга")).append("\n\n")
                .append("Пилотна цена: ").append(offer.optInt("pilot_price_eur", 0)).append(" €\n")
                .append("Стандартна настройка: ").append(offer.optInt("standard_setup_price_eur", 0)).append(" €\n")
                .append("Поддръжка: ").append(offer.optInt("monthly_support_price_eur", 0)).append(" €/месец\n\n")
                .append("Какво включва:\n");
        if (scope != null) {
            for (int i = 0; i < scope.length(); i++) {
                message.append("• ").append(scope.optString(i)).append("\n");
            }
        }
        message.append("\nЦената е наша тестова оферта, не потвърден бюджет на клиент. Обхватът и условията се договарят предварително.");
        new AlertDialog.Builder(this)
                .setTitle("Нашата услуга")
                .setMessage(message.toString())
                .setPositiveButton("Затвори", null)
                .show();
    }

    private void card(LinearLayout parent, String label,
                      String value, int valueColor) {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(16), dp(14), dp(16), dp(14));
        box.setBackground(background(PANEL, 16));

        TextView heading = text(label, 12, MUTED, true);
        TextView amount = text(value, 23, valueColor, true);

        box.addView(heading);
        space(box, 5);
        box.addView(amount);

        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                -1, -2);
        lp.bottomMargin = dp(10);
        parent.addView(box, lp);
    }

    private void section(String title) {
        TextView heading = text(title, 14, GREEN, true);
        heading.setPadding(0, dp(18), 0, dp(10));
        content.addView(heading);
    }

    private void actionButton(String label, View.OnClickListener listener) {
        Button button = new Button(this);
        button.setText(label);
        button.setTextColor(WHITE);
        button.setAllCaps(false);
        button.setTextSize(15);
        button.setGravity(Gravity.CENTER_VERTICAL);
        button.setBackground(background(PANEL, 12));
        button.setOnClickListener(listener);

        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                -1, dp(54));
        lp.bottomMargin = dp(8);
        content.addView(button, lp);
    }

    private void addTransaction(String type) {
        LinearLayout form = new LinearLayout(this);
        form.setOrientation(LinearLayout.VERTICAL);
        form.setPadding(dp(8), dp(4), dp(8), dp(4));

        EditText name = new EditText(this);
        name.setSingleLine(true);
        name.setHint("Описание");
        name.setHintTextColor(MUTED);
        name.setTextColor(WHITE);
        form.addView(name);

        EditText amount = new EditText(this);
        amount.setSingleLine(true);
        amount.setHint("Сума в евро");
        amount.setHintTextColor(MUTED);
        amount.setTextColor(WHITE);
        amount.setInputType(8194);
        form.addView(amount);

        new AlertDialog.Builder(this)
                .setTitle(type)
                .setView(form)
                .setNegativeButton("Отказ", null)
                .setPositiveButton("Запази", (dialog, which) -> {
                    String description = name.getText().toString().trim();
                    double value = parseAmount(amount.getText().toString());

                    if (description.isEmpty() || value <= 0) {
                        toast("Въведи описание и валидна сума.");
                        return;
                    }

                    JSONObject item = new JSONObject();
                    try {
                        item.put("type", type);
                        item.put("name", description);
                        item.put("amount", value);
                        item.put("created_at", new SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.ROOT).format(new Date()));
                        transactions.put(item);

                        if (type.equals("Приход")) {
                            cash += value;
                        } else {
                            cash -= value;
                        }

                        saveData();
                        renderDashboard();
                        toast("Операцията е запазена.");
                    } catch (Exception e) {
                        toast("Грешка при запазването.");
                    }
                })
                .show();
    }

    private void addItem(String type) {
        LinearLayout form = new LinearLayout(this);
        form.setOrientation(LinearLayout.VERTICAL);
        form.setPadding(dp(8), dp(4), dp(8), dp(4));

        EditText name = new EditText(this);
        name.setSingleLine(true);
        name.setHint("Описание");
        name.setHintTextColor(MUTED);
        name.setTextColor(WHITE);
        form.addView(name);

        EditText amount = new EditText(this);
        amount.setSingleLine(true);
        amount.setHint("Стойност в евро");
        amount.setHintTextColor(MUTED);
        amount.setTextColor(WHITE);
        amount.setInputType(8194);
        form.addView(amount);

        new AlertDialog.Builder(this)
                .setTitle(type)
                .setView(form)
                .setNegativeButton("Отказ", null)
                .setPositiveButton("Запази", (dialog, which) -> {
                    String description = name.getText().toString().trim();
                    double value = parseAmount(amount.getText().toString());

                    if (description.isEmpty() || value <= 0) {
                        toast("Въведи описание и валидна сума.");
                        return;
                    }

                    JSONObject item = new JSONObject();
                    try {
                        item.put("name", description);
                        item.put("amount", value);

                        if (type.equals("Актив")) {
                            assets.put(item);
                        } else {
                            debts.put(item);
                        }

                        saveData();
                        renderDashboard();
                        toast("Запазено успешно.");
                    } catch (Exception e) {
                        toast("Грешка при запазването.");
                    }
                })
                .show();
    }

    private void setCash() {
        EditText input = new EditText(this);
        input.setSingleLine(true);
        input.setHint("Начална наличност в евро");
        input.setHintTextColor(MUTED);
        input.setTextColor(WHITE);
        input.setInputType(8194);
        input.setText(String.valueOf(cash));

        new AlertDialog.Builder(this)
                .setTitle("Начална наличност")
                .setView(input)
                .setNegativeButton("Отказ", null)
                .setPositiveButton("Запази", (dialog, which) -> {
                    try {
                        double entered = Double.parseDouble(
                                input.getText().toString().trim().replace(",", "."));
                        if (!Double.isFinite(entered) || entered < 0) {
                            toast("Въведи валидна неотрицателна сума.");
                            return;
                        }
                        cash = entered;
                        saveData();
                        renderDashboard();
                        toast("Наличността е обновена.");
                    } catch (Exception e) {
                        toast("Въведи валидна сума.");
                    }
                })
                .show();
    }

    private void showTransactions() {
        StringBuilder result = new StringBuilder();

        for (int i = transactions.length() - 1; i >= 0; i--) {
            JSONObject item = transactions.optJSONObject(i);
            if (item != null) {
                result.append(item.optString("type")).append(": ")
                        .append(item.optString("name")).append(" — ")
                        .append(money.format(item.optDouble("amount", 0)))
                        .append("\n\n");
            }
        }

        if (result.length() == 0) {
            result.append("Няма записани операции.");
        }

        new AlertDialog.Builder(this)
                .setTitle("История")
                .setMessage(result.toString())
                .setPositiveButton("Затвори", null)
                .show();
    }

    private void showAnalysis() {
        double income = sumTransactions("Приход");
        double expenses = sumTransactions("Разход");
        double assetTotal = sumItems(assets);
        double debtTotal = sumItems(debts);
        double netWorth = cash + assetTotal - debtTotal;

        String advice;
        if (expenses > income && income > 0) {
            advice = "Разходите са по-високи от приходите. Прегледай бюджета.";
        } else if (income == 0 && expenses > 0) {
            advice = "Записани са разходи, но няма отчетени приходи.";
        } else if (income > expenses) {
            advice = "Отчетените приходи надвишават разходите.";
        } else {
            advice = "Добави реалните си приходи и разходи за по-полезен анализ.";
        }

        String report =
                "Наличност: " + money.format(cash) + "\n" +
                "Приходи: " + money.format(income) + "\n" +
                "Разходи: " + money.format(expenses) + "\n" +
                "Активи: " + money.format(assetTotal) + "\n" +
                "Дългове: " + money.format(debtTotal) + "\n" +
                "Нетна стойност: " + money.format(netWorth) + "\n\n" +
                "Оценка: " + advice + "\n\n" +
                "Анализът използва само данните, които си въвел. " +
                "Не е инвестиционна или данъчна препоръка.";

        new AlertDialog.Builder(this)
                .setTitle("Финансов анализ")
                .setMessage(report)
                .setPositiveButton("Затвори", null)
                .show();
    }

    private double sumTransactions(String type) {
        double total = 0;
        for (int i = 0; i < transactions.length(); i++) {
            JSONObject item = transactions.optJSONObject(i);
            if (item != null && type.equals(item.optString("type"))) {
                total += item.optDouble("amount", 0);
            }
        }
        return total;
    }

    private double sumItems(JSONArray list) {
        double total = 0;
        for (int i = 0; i < list.length(); i++) {
            JSONObject item = list.optJSONObject(i);
            if (item != null) {
                total += item.optDouble("amount", 0);
            }
        }
        return total;
    }

    private double parseAmount(String value) {
        try {
            double parsed = Double.parseDouble(value.trim().replace(",", "."));
            return Double.isFinite(parsed) && parsed > 0 ? parsed : 0;
        } catch (Exception e) {
            return 0;
        }
    }

    private TextView text(String value, int size, int color, boolean bold) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextSize(size);
        view.setTextColor(color);
        if (bold) {
            view.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        }
        return view;
    }

    private GradientDrawable background(int color, int radius) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(color);
        drawable.setCornerRadius(dp(radius));
        return drawable;
    }

    private void space(LinearLayout parent, int height) {
        View view = new View(this);
        parent.addView(view, new LinearLayout.LayoutParams(1, dp(height)));
    }

    private int dp(int value) {
        return (int) (value * getResources().getDisplayMetrics().density + 0.5f);
    }

    private void toast(String message) {
        Toast.makeText(this, message, Toast.LENGTH_SHORT).show();
    }
}
