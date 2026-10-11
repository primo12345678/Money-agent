
package com.moneyagent;

import android.app.Activity;
import android.app.AlertDialog;
import android.os.Bundle;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.content.SharedPreferences;
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

    private final NumberFormat money =
            NumberFormat.getCurrencyInstance(new Locale("bg", "BG"));

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
    }

    private void renderDashboard() {
        content.removeAllViews();

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
        content.addView(box, lp);
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
        amount.setHint("Сума в лева");
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
        amount.setHint("Стойност в лева");
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
        input.setHint("Начална наличност в лева");
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
                        cash = Double.parseDouble(
                                input.getText().toString().trim()
                                        .replace(",", "."));
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
            return Double.parseDouble(value.trim().replace(",", "."));
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
